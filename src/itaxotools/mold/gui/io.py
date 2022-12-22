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

from typing import Callable
import io
import sys


class StreamMultiplexer(io.TextIOBase):
    def __init__(self, *streams):
        super().__init__()
        self.streams = []

        for stream in streams:
            self.add(stream)

    def add(self, stream):
        if stream:  # stdio streams might be None if compiled
            self.streams.append(stream)

    def remove(self, stream):
        self.streams.remove(stream)

    def close(self):
        for stream in self.streams:
            if stream not in [sys.stdout, sys.stderr]:
                stream.close()

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def seekable(self):
        return False

    def readable(self):
        return all(stream.readable for stream in self.streams)

    def read(self, *args, **kwargs):
        for stream in self.streams:
            stream.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        for stream in self.streams:
            stream.readline(*args, **kwargs)

    def readlines(self, *args, **kwargs):
        for stream in self.streams:
            stream.readlines(*args, **kwargs)

    def writable(self):
        return all(stream.writable for stream in self.streams)

    def write(self, *args, **kwargs):
        for stream in self.streams:
            stream.write(*args, **kwargs)

    def writeline(self, *args, **kwargs):
        for stream in self.streams:
            stream.writeline(*args, **kwargs)

    def writelines(self, *args, **kwargs):
        for stream in self.streams:
            stream.writelines(*args, **kwargs)


class WriterIO(io.TextIOBase):
    """File-like object that only writes by calling a function"""

    def __init__(self, func: Callable[[str], None]):
        super().__init__()
        self.func = func

    def close(self):
        pass

    def flush(self):
        pass

    def readable(self):
        return False

    def writable(self):
        return True

    def write(self, text):
        self.func(text)

    def writeline(self, line):
        self.write(line+'\n')

    def writelines(self, lines):
        for line in lines:
            self.writeline(line)
