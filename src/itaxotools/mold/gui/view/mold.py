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

from PySide6 import QtCore, QtWidgets, QtGui

from pathlib import Path

from itaxotools.common.utility import AttrDict, override
from itaxotools.common.widgets import VLineSeparator

from .. import app
from ..types import TaxonSelectMode, PairwiseSelectMode
from .common import Card, TaskView, GLineEdit, GTextEdit, LongLabel, RadioButtonGroup


def is_fasta(path):
    with open(path) as file:
        char = file.read(1)
        return char == '>'


class GrowingTextEdit(GTextEdit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.document().contentsChanged.connect(self.updateGeometry)
        self.height_slack = 16
        self.lines_max = 8

    def getHeightHint(self):
        lines = self.document().size().height()
        lines = min(lines, self.lines_max)
        height = self.fontMetrics().height()
        return int(lines * height)

    def sizeHint(self):
        width = super().sizeHint().width()
        height = self.getHeightHint() + 16
        return QtCore.QSize(width, height)


class TitleCard(Card):
    run = QtCore.Signal()
    cancel = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        description = LongLabel(
            'Identify diagnostic nucleotide combinations (DNCs) in DNA sequence alignments, which can be used to provide formal diagnoses of these taxa. This is in the form of "redundant DNC” (rDNC), which takes into account unsampled genetic diversity.')

        citations = LongLabel(
            'Fedosov A.E., Achaz G., Gontchar A., Puillandre N. 2022. MOLD, a novel software to compile accurate and reliable DNA diagnoses for taxonomic descriptions. Molecular Ecology Resources, DOI: 10.1111/1755-0998.13590.')
        citations.setStyleSheet("LongLabel {color: Palette(Dark)}")

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(description)
        contents.addWidget(citations)
        contents.addStretch(1)
        contents.setSpacing(12)

        manual = QtWidgets.QPushButton('Manual')
        galaxy = QtWidgets.QPushButton('Galaxy')
        homepage = QtWidgets.QPushButton('Homepage')
        itaxotools = QtWidgets.QPushButton('iTaxoTools')
        itaxotools.setFixedWidth(100)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(manual)
        buttons.addWidget(galaxy)
        buttons.addWidget(homepage)
        buttons.addWidget(itaxotools)
        buttons.addStretch(1)
        buttons.setSpacing(8)

        separator = VLineSeparator(1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons, 0)
        layout.addWidget(separator, 0)
        layout.addLayout(contents, 1)
        layout.setSpacing(16)
        self.addLayout(layout)


class InputSelector(Card):
    browse = QtCore.Signal()

    def __init__(self, label_text, placeholder_text, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel(label_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setFixedWidth(174)

        filename = GLineEdit()
        filename.setReadOnly(True)
        filename.setPlaceholderText(placeholder_text)
        filename.setStyleSheet("""
            QLineEdit {
                background-color: palette(Base);
                padding: 2px 4px 2px 4px;
                border-radius: 4px;
                border: 1px solid palette(Mid);
                }
            """)

        browse = QtWidgets.QPushButton('Browse')
        browse.clicked.connect(self.browse)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(32)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addWidget(filename, 1)
        layout.addWidget(browse)
        self.addLayout(layout)

        self.controls.label = label
        self.controls.filename = filename
        self.controls.browse = browse

    def setPath(self, path):
        if path is None:
            self.controls.filename.setText('')
        else:
            self.controls.filename.setText(str(path))


class ConfigSelector(InputSelector):
    def __init__(self, parent=None):
        super().__init__('Configuration File', 'Load options from a file', parent)


class SequenceSelector(InputSelector):
    def __init__(self, parent=None):
        super().__init__('Sequence Data File', 'To begin, open a Fasta file that includes taxon identifiers', parent)


class ModeSelector(Card):
    toggled = QtCore.Signal()

    def __init__(self, mode_text, mode_type, line_text, list_text, parent=None):
        super().__init__(parent)
        self.draw_modes(mode_text, mode_type)
        self.draw_line(line_text)
        self.draw_list(list_text)

    def draw_modes(self, mode_text, mode_type):
        label = QtWidgets.QLabel(mode_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setFixedWidth(174)

        group = RadioButtonGroup()
        group.valueChanged.connect(self.handleToggle)
        self.controls.mode = group

        radios = QtWidgets.QHBoxLayout()
        radios.setContentsMargins(0, 0, 0, 0)
        radios.setSpacing(32)
        for mode in mode_type:
            button = QtWidgets.QRadioButton(str(mode))
            radios.addWidget(button)
            group.add(button, mode)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(32)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(radios, 3)
        layout.addStretch(1)
        self.addLayout(layout)

    def draw_line(self, line_text):
        label = QtWidgets.QLabel(line_text)
        label.setWordWrap(True)

        line = GLineEdit()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addWidget(line, 1)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.section_line = widget
        self.controls.line = line

    def draw_list(self, list_text):
        label = QtWidgets.QLabel(list_text)
        label.setWordWrap(True)
        label.setFixedWidth(174)
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        list = GrowingTextEdit()

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(32)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addWidget(list, 1)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.section_list = widget
        self.controls.list = list

    def setMode(self, mode):
        self.controls.mode.setValue(mode)
        QtCore.QTimer.singleShot(10, self.update)

    def handleToggle(self, mode):
        self.controls.section_line.setVisible(True)
        self.controls.section_list.setVisible(True)


class TaxonSelector(ModeSelector):
    def __init__(self, parent=None):
        super().__init__(
            mode_text = 'Taxon Selection',
            mode_type = TaxonSelectMode,
            line_text = 'List of taxa (comma-separated) that will be used as the qTaxa parameter of the active configuration:',
            list_text = (
                'Enter a list of taxa, separated either by new lines or commas. \n\n'
                'Combine taxa using the plus ("+") symbol.'
            ),
            parent = parent,
        )

    def handleToggle(self, mode):
        self.controls.section_line.setVisible(mode == TaxonSelectMode.Line)
        self.controls.section_list.setVisible(mode == TaxonSelectMode.List)


class PairwiseSelector(ModeSelector):
    def __init__(self, parent=None):
        super().__init__(
            mode_text = 'Pairwise Selection',
            mode_type = PairwiseSelectMode,
            line_text = (
                'List of taxon pairs (comma-separated) that will be used as the qTaxa parameter of the active configuration. '
                'This is appended to any other qTaxa options from taxon selection above.'
            ),
            list_text = (
                'Enter a list of taxon pairs, separated either by new lines or commas. \n\n'
                'Combine taxa using the plus ("+") symbol.'
            ),
            parent = parent,
        )

    def handleToggle(self, mode):
        self.controls.section_line.setVisible(mode == PairwiseSelectMode.Line)
        self.controls.section_list.setVisible(mode == PairwiseSelectMode.List)


class MoldView(TaskView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.configuration = ConfigSelector(self)
        self.cards.sequence = SequenceSelector(self)
        self.cards.taxa = TaxonSelector(self)
        self.cards.pairs = PairwiseSelector(self)

        layout = QtWidgets.QVBoxLayout()
        for card in self.cards:
            layout.addWidget(card)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def setObject(self, object):
        self.object = object
        self.binder.unbind_all()

        self.binder.bind(self.cards.configuration.browse, self.openConfiguration)
        self.binder.bind(self.cards.sequence.browse, self.openSequence)

        self.binder.bind(object.notification, self.showNotification)
        # self.bind(object.progression, self.cards.progress.showProgress)

        self.binder.bind(object.properties.configuration_path, self.cards.configuration.setVisible, lambda path: path is not None)
        self.binder.bind(object.properties.configuration_path, self.cards.configuration.setPath)
        self.binder.bind(object.properties.sequence_path, self.cards.sequence.setPath)

        self.binder.bind(self.cards.taxa.toggled, object.properties.taxon_mode)
        self.binder.bind(object.properties.taxon_mode, self.cards.taxa.setMode)
        self.binder.bind(self.cards.taxa.controls.line.textEditedSafe, object.properties.taxon_line)
        self.binder.bind(object.properties.taxon_line, self.cards.taxa.controls.line.setText)
        self.binder.bind(self.cards.taxa.controls.list.textEditedSafe, object.properties.taxon_list)
        self.binder.bind(object.properties.taxon_list, self.cards.taxa.controls.list.setText)

        self.binder.bind(self.cards.pairs.toggled, object.properties.pairs_mode)
        self.binder.bind(object.properties.pairs_mode, self.cards.pairs.setMode)
        self.binder.bind(self.cards.pairs.controls.line.textEditedSafe, object.properties.pairs_line)
        self.binder.bind(object.properties.pairs_line, self.cards.pairs.controls.line.setText)
        self.binder.bind(self.cards.pairs.controls.list.textEditedSafe, object.properties.pairs_list)
        self.binder.bind(object.properties.pairs_list, self.cards.pairs.controls.list.setText)

    def open(self):
        path = self.getOpenPath()
        if path is None:
            return
        if is_fasta(path):
            self.object.open_sequence_path(path)
        else:
            self.object.open_configuration_path(path)

    def openConfiguration(self):
        path = self.getOpenPath()
        if path is not None:
            self.object.open_configuration_path(path)

    def openSequence(self):
        path = self.getOpenPath()
        if path is not None:
            self.object.open_sequence_path(path)

    def save(self):
        path = self.getSavePath('Save all')
        self.object.save(path)
