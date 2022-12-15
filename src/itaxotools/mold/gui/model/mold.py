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
from ..types import Notification
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
    sequence_path = Property(Path, None)

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

    def open_configuration_path(self, path):
        error_caption = 'Error opening configuration file: \n'

        params = {}
        with open(path) as file:
            for line in file:
                line = line.strip()
                if line.startswith('#'):
                    continue
                split = line.split('=')
                if len(split) == 2 and len(split[1]) != 0:
                    params[split[0]] = split[1].replace(' ', '')

        if not params:
            self.notification.emit(Notification.Fail(
                error_caption + f'No parameters found in file: {str(path)}'))
            return

        for param in params:
            if not param.upper() in [
                'GAPS_AS_CHARS',
                'QTAXA',
                'TAXON_RANK',
                'INPUT_FILE',
                'ORIG_FNAME',
                'CUTOFF',
                'NUMBERN',
                'NUMBER_OF_ITERATIONS',
                'MAXLEN1',
                'MAXLEN2',
                'IREF',
                'PDIFF',
                'NMAXSEQ',
                'SCORING',
                'OUTPUT_FILE',
            ]:
                self.notification.emit(Notification.Fail(
                    error_caption + f'Invalid parameter name: {param}'))
                return

        for key, value in params.items():
            print(key.upper(), '=', value)

        self.configuration_path = path

    def open_sequence_path(self, path):
        error_caption = 'Error opening sequence file: \n'

        with open(path) as file:
            char = file.read(1)
            if char != '>':
                self.notification.emit(Notification.Fail(
                    error_caption + 'Sequences must be provided in the Fasta format, and the file must begin with the ">" symbol'))
                return

            line = file.readline()
            split = line.split('|')
            if len(split) < 2:
                self.notification.emit(Notification.Fail(
                    error_caption + 'Taxon identifiers must be provided after each sequence identifier, separated by a single pipe symbol: "|"'))
                return
            elif len(split) > 2:
                self.notification.emit(Notification.Fail(
                    error_caption + 'Each identifier line must only contain a single pipe symbol: "|"'))
                return

        self.sequence_path = path

    def save(self, path):
        print('save', path)
