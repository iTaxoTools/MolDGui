# -----------------------------------------------------------------------------
# MolDGui - Module and Gui for MolD
# Copyright (C) 2022  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from PySide6 import QtCore

from collections import deque
from typing import Callable
import multiprocessing as mp
import sys
import io

from itaxotools.common.utility import override

from .io import StreamMultiplexer
from .threading_loop import (
    Command, InitDone, ReportProgress, ReportDone, ReportFail, ReportExit, ReportReset, ReportQuit, loop)


class Worker(QtCore.QThread):
    """Execute functions on a child process, get notified with results"""
    done = QtCore.Signal(ReportDone)
    fail = QtCore.Signal(ReportFail)
    error = QtCore.Signal(ReportExit)
    progress = QtCore.Signal(ReportProgress)

    def __init__(self, name='Worker', eager=True):
        """Immediately starts thread execution"""
        super().__init__()
        self.eager = eager
        self.name = name

        self.queue = mp.Queue()
        self.pipeIn = None
        self.pipeOut = None
        self.pipeErr = None
        self.commands = None
        self.results = None
        self.reports = None
        self.process = None
        self.resetting = False
        self.quitting = False

        self.streamOut = StreamMultiplexer(sys.stdout)
        self.streamErr = StreamMultiplexer(sys.stderr)

        self.logFileAll = None
        self.logPathExec = None
        self.logFileExec = None

        app = QtCore.QCoreApplication.instance()
        app.aboutToQuit.connect(self.quit)

        self.start()

    @override
    def run(self):
        """
        Internal. This is executed on the new thread after start() is called.
        Once a child process is ready, enter an event loop.
        """
        if self.eager:
            self.process_start()
        while not self.quitting:
            task = self.queue.get()
            if task is None:
                break
            if self.process is None:
                self.process_start()
            # make context manager?
            # self.openLogFileExec(task.id)
            self.commands.send(task)
            report = self.loop(task)
            self.handle_report(report)
            # self.closeLogFileExec()

    def loop(self, task: Command):
        """
        Internal. Thread event loop that handles events
        for the currently running process.
        """
        sentinel = self.process.sentinel
        waitList = {
            sentinel: None,
            self.results: None,
            self.reports: self.progress.emit,
            self.pipeOut: self.streamOut.write,
            self.pipeErr: self.streamErr.write,
        }
        report = None
        while not report:
            readyList = mp.connection.wait(waitList.keys())
            if sentinel in readyList:
                waitList.pop(sentinel, None)
                waitList.pop(self.results, None)
                report = self.handle_exit(task, waitList)
            elif self.results in readyList:
                try:
                    report = self.results.recv()
                except EOFError:
                    waitList.pop(self.results, None)
                else:
                    waitList.pop(sentinel, None)
                    waitList.pop(self.results, None)
                    self.consume_connections(waitList)
            else:
                self.handle_connections(waitList, readyList)
        return report

    def handle_exit(self, task, waitList):

        self.consume_connections(waitList)
        exitcode = self.process.exitcode
        resetting = self.resetting

        self.pipeIn.close()
        self.pipeOut.close()
        self.pipeErr.close()
        self.commands.close()
        self.results.close()
        self.reports.close()
        self.process = None

        if self.quitting:
            return ReportQuit()
        elif self.eager:
            self.process_start()

        if resetting:
            return ReportReset(task.id)

        return ReportExit(task.id, exitcode)

    def handle_connections(self, waitList, readyList):
        for connection in readyList:
            try:
                data = connection.recv()
            except EOFError:
                waitList.pop(connection)
            else:
                waitList[connection](data)

    def consume_connections(self, waitList):
        while readyList := mp.connection.wait(waitList.keys(), 0):
            self.handle_connections(waitList, readyList)

    def handle_report(self, report):
        self.streamOut.flush()
        self.streamErr.flush()
        if isinstance(report, ReportDone):
            self.done.emit(report)
        elif isinstance(report, ReportFail):
            self.fail.emit(report)
        elif isinstance(report, ReportExit):
            if report.id != 0:
                self.error.emit(report)

    def setLogPathAll(self, path):
        if self.logFileAll:
            self.streamOut.remove(self.logFileAll)
            self.streamErr.remove(self.logFileAll)
            self.logFileAll.close()
        self.logFileAll = open(path, 'a')
        self.streamOut.add(self.logFileAll)
        self.streamErr.add(self.logFileAll)

    def setLogPathExec(self, path):
        self.logPathExec = path

    def openLogFileExec(self, id):
        path = self.logPathExec
        if not path:
            return None
        path = path.parent / path.name.format(str(id))
        self.logFileExec = open(path, 'a')
        self.streamOut.add(self.logFileExec)
        self.streamErr.add(self.logFileExec)

    def closeLogFileExec(self):
        if self.logFileExec:
            self.streamOut.remove(self.logFileExec)
            self.streamErr.remove(self.logFileExec)
            self.logFileExec.close()

    def process_start(self):
        """Internal. Initialize process and pipes"""
        self.resetting = False
        pipeIn, self.pipeIn = mp.Pipe(duplex=False)
        self.pipeOut, pipeOut = mp.Pipe(duplex=False)
        self.pipeErr, pipeErr = mp.Pipe(duplex=False)
        commands, self.commands = mp.Pipe(duplex=False)
        self.results, results = mp.Pipe(duplex=False)
        self.reports, reports = mp.Pipe(duplex=False)
        self.process = mp.Process(
            target=loop, daemon=True, name=self.name,
            args=(commands, results, reports, pipeIn, pipeOut, pipeErr))
        self.process.start()

    def exec(self, id, function, *args, **kwargs):
        """Execute given function on a child process"""
        self.queue.put(Command(id, function, args, kwargs))

    def reset(self):
        """Interrupt the current task"""
        if self.process is not None and self.process.is_alive():
            self.resetting = True
            self.streamOut.flush()
            self.streamErr.flush()
            self.process.terminate()

    @override
    def quit(self):
        """Also kills the child process"""
        self.reset()
        self.quitting = True
        self.queue.put(None)

        super().quit()
        self.wait()
        self.streamOut.close()
        self.streamErr.close()
