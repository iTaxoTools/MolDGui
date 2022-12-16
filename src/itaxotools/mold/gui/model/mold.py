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

from itaxotools.mold import main

from ..files import check_sequence_file, parse_configuration_file
from ..utility import Property, Instance
from ..types import Notification, TaxonSelectMode, PairwiseSelectMode, TaxonRank, GapsAsCharacters
from .common import Task


def dummy_process(**kwargs):
    import time
    import itaxotools
    for k, v in kwargs.items():
        print(k, '=', v)
    print('...')
    for x in range(100):
        itaxotools.progress_handler(text='dummy', value=x+1, maximum=100)
        time.sleep(0.02)

    print('Done!~')
    return 42


class MoldModel(Task):
    configuration_path = Property(Path, None)
    sequence_path = Property(Path, None)

    taxon_mode = Property(TaxonSelectMode, TaxonSelectMode.All)
    taxon_line = Property(str, '')
    taxon_list = Property(str, '')

    pairs_mode = Property(PairwiseSelectMode, PairwiseSelectMode.All)
    pairs_line = Property(str, '')
    pairs_list = Property(str, '')

    taxon_rank = Property(TaxonRank, TaxonRank.Species)
    gaps_as_characters = Property(GapsAsCharacters, GapsAsCharacters.Yes)


    def __init__(self, name=None):
        super().__init__(name)

        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

    def readyTriggers(self):
        return [
            self.properties.sequence_path,
            self.properties.taxon_mode,
            self.properties.taxon_line,
            self.properties.taxon_list,
            self.properties.pairs_mode,
            self.properties.pairs_line,
            self.properties.pairs_list,
        ]

    def isReady(self):
        if not self.sequence_path:
            return False
        if self.taxon_mode == TaxonSelectMode.Line:
            if self.taxon_line == '':
                return False
        if self.taxon_mode == TaxonSelectMode.List:
            if self.taxon_list == '':
                return False
        if self.pairs_mode == PairwiseSelectMode.Line:
            if self.pairs_line == '':
                return False
        if self.pairs_mode == PairwiseSelectMode.List:
            if self.pairs_list == '':
                return False
        return True

    def start(self):
        self.busy = True
        self.busy_main = True
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        qTaxa = []
        if self.taxon_mode == TaxonSelectMode.All:
            qTaxa.append('ALL')
        elif self.taxon_mode == TaxonSelectMode.Line:
            qTaxa.append(self.taxon_line)
        elif self.taxon_mode == TaxonSelectMode.List:
            qTaxa.append(self.taxon_list.replace('\n', ','))

        if self.pairs_mode == PairwiseSelectMode.All:
            qTaxa.append('ALLVSALL')
        elif self.pairs_mode == PairwiseSelectMode.Line:
            qTaxa.append(self.pairs_line)
        elif self.pairs_mode == PairwiseSelectMode.List:
            qTaxa.append(self.pairs_list.replace('\n', ','))

        self.exec(
            None,
            dummy_process,
            tmpfname=str(self.sequence_path),
            taxalist=','.join(qTaxa),
            taxonrank=self.taxon_rank.code,
            gapsaschars=self.gaps_as_characters.code,
        )

    def open_configuration_path(self, path):
        try:
            params = parse_configuration_file(path)
            for key, value in params.items():
                print(key.upper(), '=', value)
            self.configuration_path = path
        except Exception as exception:
            self.notification.emit(Notification.Fail(str(exception)))

    def open_sequence_path(self, path):
        try:
            check_sequence_file(path)
            self.sequence_path = path
        except Exception as exception:
            self.notification.emit(Notification.Fail(str(exception)))

    def save(self, path):
        print('save', path)
