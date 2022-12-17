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

import itertools
from collections import defaultdict
from typing import Any, Callable, List

from itaxotools.common.utility import override

from ..threading import ReportProgress, ReportDone, ReportFail, ReportError, Worker
from ..types import Notification, Type
from ..utility import Property, PropertyObject, PropertyRef


class _TypedPropertyObjectMeta(type(PropertyObject), type(Type)):
    def __new__(cls, name, bases, attrs):
        obj = super().__new__(cls, name, bases, attrs)
        return cls._patch_object(obj, name, bases)


class Object(PropertyObject, Type, metaclass=_TypedPropertyObjectMeta):
    """Interface for backend structures"""
    name = Property(str, '')

    def __init__(self, name=None):
        super().__init__()
        if name:
            self.name = name

    def __repr__(self):
        return Type.__repr__(self)

    def __eq__(self, other):
        return id(self) == id(other)


class Task(Object):
    task_name = 'Task'

    notification = QtCore.Signal(Notification)
    progression = QtCore.Signal(ReportProgress)

    ready = Property(bool, True)
    busy = Property(bool, False)
    done = Property(bool, False)
    editable = Property(bool, True)

    counters = defaultdict(lambda: itertools.count(1, 1))

    def __init__(self, name=None, init=None):
        super().__init__(name or self._get_next_name())

        self.worker = Worker(name=self.name, eager=True, init=init)
        self.worker.done.connect(self.onDone)
        self.worker.fail.connect(self.onFail)
        self.worker.error.connect(self.onError)
        self.worker.progress.connect(self.onProgress)

        for property in self.readyTriggers():
            property.notify.connect(self.checkIfReady)

        for property in [
            self.properties.busy,
            self.properties.done,
        ]:
            property.notify.connect(self.checkEditable)

    @classmethod
    def _get_next_name(cls):
        return f'{cls.task_name} #{next(cls.counters[cls.task_name])}'

    def __str__(self):
        return f'{self.task_name}({repr(self.name)})'

    def __repr__(self):
        return str(self)

    def onProgress(self, report: ReportProgress):
        self.progression.emit(report)

    def onFail(self, report: ReportFail):
        print(str(report.exception))
        print(report.traceback)
        self.notification.emit(Notification.Fail(str(report.exception), report.traceback))
        self.busy = False

    def onError(self, report: ReportError):
        self.notification.emit(Notification.Fail(f'Process failed with exit code: {report.exit_code}'))
        self.busy = False

    def onDone(self, report: ReportDone):
        """Overload this to handle results"""
        self.notification.emit(Notification.Info(f'{self.name} completed successfully!'))
        self.busy = False
        self.done = True

    def start(self):
        """Slot for starting the task"""
        print('OHAI')
        self.busy = True
        self.run()

    def stop(self):
        """Slot for interrupting the task"""
        if self.worker is None:
            return
        self.worker.reset()
        self.notification.emit(Notification.Warn('Cancelled by user.'))
        self.busy = False

    def readyTriggers(self) -> List[PropertyRef]:
        """Overload this to set properties as ready triggers"""
        return []

    def checkIfReady(self, *args):
        """Slot to check if ready"""
        self.ready = self.isReady()

    def isReady(self) -> bool:
        """Overload this to check if ready"""
        return False

    def checkEditable(self):
        self.editable = not (self.busy or self.done)

    def run(self):
        """Called by start(). Overload this with calls to exec()"""
        self.exec(lambda *args: None)

    def exec(self, id: Any, task: Callable, *args, **kwargs):
        """Call this from run() to execute tasks"""
        self.worker.exec(id, task, *args, **kwargs)
