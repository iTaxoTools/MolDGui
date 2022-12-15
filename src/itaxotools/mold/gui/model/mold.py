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

from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path

from ..utility import Property, Instance
from .common import Task


def dummy_process(**kwargs):
    import time
    import itaxotools
    for k, v in kwargs.items():
        print(k, v)
    print('...')
    for x in range(100):
        itaxotools.progress_handler(text='dummy', value=x+1, maximum=100)
        time.sleep(0.02)

    print('Done!~')
    return 42


class MoldModel(Task):
    configuration_path = Property(Path, None)
    sequence_path = Property(Path, Path('samples/foo.fas'))

    def __init__(self, name=None):
        super().__init__(name)

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

    def start(self):
        self.busy = True
        self.busy_main = True
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        self.exec(
            None,
            dummy_process,
            foo=42
        )

    def open_configuration(self, path):
        self.configuration_path = path

    def open_sequence(self, path):
        self.sequence_path = path

    def save(self, path):
        print('save', path)
