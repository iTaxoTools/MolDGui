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
from ..utility import Property, Instance, Binder, PropertyObject, EnumObject
from ..types import AdvancedMDNCProperties, AdvancedRDNSProperties, Notification, TaxonSelectMode, PairwiseSelectMode, TaxonRank, GapsAsCharacters, MoldResults
from ..io import WriterIO
from .common import Task


def condense(text: str, separator: str):
    split = text.split(separator)
    stripped = (x.strip() for x in split)
    return separator.join(stripped)


def inflate(text: str, separator: str):
    split = text.split(separator)
    stripped = (x.strip() for x in split)
    return f' {separator} '.join(stripped)


def main_wrapper(workdir: Path, confdir: Path, input_path: Path, **kwargs):
    from itaxotools.mold import main

    output_path = workdir / 'out.html'
    pairwise_path = workdir / 'out_pairwise.html'

    if confdir and not input_path.exists() and not input_path.is_absolute():
        input_path = confdir / input_path

    print('  PARAMETERS FROM GUI  '.center(58, '#'))
    print('')
    print('tmpfname', '=', input_path)
    print('outfname', '=', output_path)
    for k,v in kwargs.items():
        print(k, '=', repr(v))
    print('')

    main(tmpfname=str(input_path), outfname=str(output_path), **kwargs)

    if not pairwise_path.exists():
        pairwise_path = None
    return MoldResults(output_path, pairwise_path)


class AdvancedDNCModel(EnumObject):
    enum = AdvancedMDNCProperties


class AdvancedRDNSModel(EnumObject):
    enum = AdvancedRDNSProperties


class MoldModel(Task):
    task_name = 'MolD'

    lineLogged = QtCore.Signal(str)
    clearLogs = QtCore.Signal()
    started = QtCore.Signal()

    configuration_path = Property(Path, None)
    sequence_path = Property(Path, None)

    taxon_mode = Property(TaxonSelectMode, TaxonSelectMode.All)
    taxon_list = Property(str, '')

    pairs_mode = Property(PairwiseSelectMode, PairwiseSelectMode.All)
    pairs_list = Property(str, '')

    taxon_rank = Property(TaxonRank, TaxonRank.Species)
    gaps_as_characters = Property(GapsAsCharacters, GapsAsCharacters.Yes)

    mdnc = Property(AdvancedDNCModel, Instance)
    rdns = Property(AdvancedRDNSModel, Instance)

    result_diagnosis = Property(Path, None)
    result_pairwise = Property(Path, None)

    suggested_diagnosis = Property(Path, None)
    suggested_pairwise = Property(Path, None)
    suggested_directory = Property(Path, None)
    dirty_data = Property(bool, False)
    has_logs = Property(bool, False)

    def __init__(self, name=None):
        super().__init__(name)
        self.temporary_directory = TemporaryDirectory(prefix=f'{self.task_name}_')
        self.temporary_path = Path(self.temporary_directory.name)

        self.textLogIO = WriterIO(self.logLine)
        self.worker.streamOut.add(self.textLogIO)
        self.worker.streamErr.add(self.textLogIO)

        # self.worker.setLogPathAll(self.temporary_path / 'all.log')
        # self.worker.setLogPathExec(self.temporary_path / '{}.log')

        self.binder = Binder()
        self.binder.bind(self.properties.sequence_path, self.properties.suggested_diagnosis,
            lambda path: None if path is None else path.parent / f'{path.stem}.molecular_diagnosis.html')
        self.binder.bind(self.properties.sequence_path, self.properties.suggested_pairwise,
            lambda path: None if path is None else path.parent / f'{path.stem}.pairwise.html')
        self.binder.bind(self.properties.sequence_path, self.properties.suggested_directory,
            lambda path: None if path is None else path.parent)

    def logLine(self, text):
        self.lineLogged.emit(text)

    def readyTriggers(self):
        return [
            self.properties.sequence_path,
            self.properties.taxon_mode,
            self.properties.taxon_list,
            self.properties.pairs_mode,
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
        if self.taxon_mode == TaxonSelectMode.List:
            if self.taxon_list == '':
                return False
        if self.pairs_mode == PairwiseSelectMode.List:
            if self.pairs_list == '':
                return False
        return True

    def start(self):
        self.clearLogs.emit()
        self.busy = True
        self.busy_main = True
        self.dirty_data = True
        self.has_logs = True

        confdir = self.configuration_path.parent if self.configuration_path else None
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        work_dir = self.temporary_path / timestamp
        work_dir.mkdir()

        qTaxa = []
        if self.taxon_mode == TaxonSelectMode.All:
            qTaxa.append('ALL')
        elif self.taxon_mode == TaxonSelectMode.List:
            qTaxa.append(self.taxon_list.replace('\n', ','))

        if self.pairs_mode == PairwiseSelectMode.All:
            qTaxa.append('ALLVSALL')
        elif self.pairs_mode == PairwiseSelectMode.List:
            qTaxa.append(self.pairs_list.replace('\n', ','))

        qTaxa = chain.from_iterable(x.split(',') for x in qTaxa)
        qTaxa = (entry.strip() for entry in qTaxa)
        qTaxa = (condense(x, 'VS') for x in qTaxa)
        qTaxa = (condense(x, '+') for x in qTaxa)
        qTaxa = (x for x in qTaxa if x)
        qTaxa = list(qTaxa)

        for property in chain(self.mdnc.properties, self.rdns.properties):
            if property.value is None or property.value == '':
                property.value = property.default

        self.exec(
            timestamp,
            main_wrapper,
            workdir = work_dir,
            confdir = confdir,
            input_path = self.sequence_path,
            taxalist = ','.join(qTaxa),
            taxonrank = self.taxon_rank.code,
            gapsaschars = self.gaps_as_characters.code,
            cutoff = self.mdnc.cutoff,
            numnucl = self.mdnc.nucleotides,
            numiter = self.mdnc.iterations,
            maxlenraw = self.mdnc.max_length_raw,
            maxlenrefined = self.mdnc.max_length_refined,
            iref = self.mdnc.indexing_reference,
            pdiff = self.rdns.p_diff or self.taxon_rank.p_diff,
            nmax = self.rdns.n_max,
            thresh = self.rdns.scoring.value,
        )

    def stop(self):
        if self.worker is None:
            return
        self.textLogIO.write('\n\nCancelled process by user request.\n')
        self.worker.reset()
        self.dirty_data = False
        self.busy = False

    def clear(self):
        self.clearLogs.emit()
        self.result_diagnosis = None
        self.result_pairwise = None
        self.dirty_data = False
        self.has_logs = False
        self.done = False

    def onDone(self, report):
        super().onDone(report)
        self.result_diagnosis = report.result.diagnosis
        self.result_pairwise = report.result.pairwise
        self.dirty_data = True

    def onFail(self, report):
        super().onFail(report)
        self.textLogIO.write(report.traceback)

    def onError(self, report):
        super().onError(report)
        self.textLogIO.write(f'Process failed with exit code: {report.exit_code}')

    def open_configuration_path(self, path):
        self.clear()
        reference = {
            'QTAXA': self.digest_qTaxa,
            'INPUT_FILE': self.properties.sequence_path.set,
            'TAXON_RANK': self.properties.taxon_rank.set,
            'GAPS_AS_CHARS': self.properties.gaps_as_characters.set,
        }
        for property in AdvancedMDNCProperties:
            reference[property.config] = self.mdnc.properties[property.key].set
        for property in AdvancedRDNSProperties:
            reference[property.config] = self.rdns.properties[property.key].set
        try:
            params = parse_configuration_file(path)
            for k, v in params.items():
                reference[k](v)
            self.configuration_path = path
        except Exception as exception:
            self.notification.emit(Notification.Fail(str(exception)))

    def open_sequence_path(self, path):
        self.clear()
        try:
            check_sequence_file(path)
            self.sequence_path = path
        except Exception as exception:
            self.notification.emit(Notification.Fail(str(exception)))

    def digest_qTaxa(self, qTaxa):
        qTaxa = qTaxa.split(',')
        qTaxa = (x.strip() for x in qTaxa)

        pairs = []
        taxa = []
        for x in qTaxa:
            if 'VS' in x:
                pairs.append(inflate(x, 'VS'))
            else:
                taxa.append(inflate(x, '+'))

        self.taxon_mode = TaxonSelectMode.List
        self.taxon_list = '\n'.join(taxa) + '\n'

        self.pairs_mode = PairwiseSelectMode.List
        self.pairs_list = '\n'.join(pairs) + '\n'

    def save_diagnosis(self, path):
        copy(self.result_diagnosis, path)

    def save_pairwise(self, path):
        copy(self.result_pairwise, path)

    def save_all(self, path):
        self.save_diagnosis(path / self.suggested_diagnosis.name)
        self.save_pairwise(path / self.suggested_pairwise.name)
        self.dirty_data = False
