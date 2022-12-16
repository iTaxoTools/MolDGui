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

from datetime import datetime
from tempfile import TemporaryDirectory
from itertools import chain
from pathlib import Path
from shutil import copy

from ..files import check_sequence_file, parse_configuration_file
from ..utility import Property, Instance, Binder
from ..types import Notification, TaxonSelectMode, PairwiseSelectMode, TaxonRank, GapsAsCharacters, MoldResults
from ..threading import TextEditLoggerIO
from .common import Task


def condense(text: str, separator: str):
    split = text.split(separator)
    stripped = (x.strip() for x in split)
    return separator.join(stripped)


def main_wrapper(workdir: Path, **kwargs):
    from itaxotools.mold import main

    output_path = workdir / 'out.html'
    pairwise_path = workdir / 'out_pairwise.html'
    main(outfname=str(output_path), **kwargs)
    if not pairwise_path.exists():
        pairwise_path = None
    return MoldResults(output_path, pairwise_path)


class MoldModel(Task):
    task_name = 'MolD'

    lineLogged = QtCore.Signal(str)
    started = QtCore.Signal()

    show_progress = Property(bool)

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

    result_diagnosis = Property(Path, None)
    result_pairwise = Property(Path, None)

    suggested_diagnosis = Property(Path, None)
    suggested_pairwise = Property(Path, None)
    suggested_directory = Property(Path, None)

    def __init__(self, name=None):
        super().__init__(name)
        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)
        self.textLogIO = TextEditLoggerIO(self.logLine)
        self.worker.setStream(self.textLogIO)

        self.binder = Binder()
        self.binder.bind(self.properties.sequence_path, self.properties.suggested_diagnosis,
            lambda path: None if path is None else path.parent / f'{path.stem}.out')
        self.binder.bind(self.properties.sequence_path, self.properties.suggested_pairwise,
            lambda path: None if path is None else path.parent / f'{path.stem}.pairwise.out')
        self.binder.bind(self.properties.sequence_path, self.properties.suggested_directory,
            lambda path: None if path is None else path.parent)

        for property in [
            self.properties.busy,
            self.properties.done,
        ]:
            property.notify.connect(self.checkProgressVisible)

    def logLine(self, text):
        self.lineLogged.emit(text)

    def checkProgressVisible(self):
        self.show_progress = self.busy or self.done

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
        if all((
            self.taxon_mode == TaxonSelectMode.No,
            self.pairs_mode == PairwiseSelectMode.No
        )):
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
        self.started.emit()

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

        qTaxa = chain.from_iterable(x.split(',') for x in qTaxa)
        qTaxa = (entry.strip() for entry in qTaxa)
        qTaxa = (condense(x, 'VS') for x in qTaxa)
        qTaxa = (condense(x, '+') for x in qTaxa)
        qTaxa = (x for x in qTaxa if x)
        qTaxa = list(qTaxa)

        self.exec(
            None,
            main_wrapper,
            workdir = work_dir,
            tmpfname = str(self.sequence_path),
            taxalist = ','.join(qTaxa),
            taxonrank = self.taxon_rank.code,
            gapsaschars = self.gaps_as_characters.code,
            cutoff = '100',
            numnucl = 5,
            numiter = 10000,
            maxlenraw = 12,
            maxlenrefined = 7,
            iref = 'NO',
            pdiff = 1 if self.taxon_rank.code == 1 else 5,
            nmax = 10,
            thresh = 75,
        )

    def onDone(self, report):
        super().onDone(report)
        self.result_diagnosis = report.result.diagnosis
        self.result_pairwise = report.result.pairwise

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

    def save_diagnosis(self, path):
        copy(self.result_diagnosis, path)

    def save_pairwise(self, path):
        copy(self.result_pairwise, path)

    def save_all(self, path):
        self.save_diagnosis(path / self.suggested_diagnosis.name)
        self.save_pairwise(path / self.suggested_pairwise.name)
