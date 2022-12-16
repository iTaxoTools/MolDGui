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
from ..types import TaxonSelectMode, PairwiseSelectMode, TaxonRank, GapsAsCharacters
from .common import Card, TaskView, GLineEdit, GTextEdit, LongLabel, RadioButtonGroup, RichRadioButton


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

        description = LongLabel(app.description)
        citations = LongLabel(app.citations)
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
        label.setFixedWidth(134)

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
        super().__init__(
            'Configuration File',
            'Load options from a file',
            parent
        )


class SequenceSelector(InputSelector):
    def __init__(self, parent=None):
        super().__init__(
            'Sequence Data File',
            'To begin, open a Fasta file that includes taxon identifiers',
            parent
        )


class ModeSelector(Card):
    toggled = QtCore.Signal(object)

    modes = []
    mode_text = 'Mode Selection'
    line_text = 'Line text:'
    list_text = 'List text.'
    line_placeholder = 'Line placeholder...'
    list_placeholder = 'List placeholder...'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_modes()
        self.draw_line()
        self.draw_list()

    def draw_modes(self):
        label = QtWidgets.QLabel(self.mode_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setFixedWidth(134)

        group = RadioButtonGroup()
        group.valueChanged.connect(self.handleToggle)
        group.valueChanged.connect(self.toggled)
        self.controls.mode = group

        radios = QtWidgets.QHBoxLayout()
        radios.setContentsMargins(0, 0, 0, 0)
        radios.setSpacing(16)
        for mode in self.modes:
            button = QtWidgets.QRadioButton(str(mode))
            radios.addWidget(button)
            group.add(button, mode)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(32)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(radios, 3)
        layout.addSpacing(32)
        self.addLayout(layout)

    def draw_line(self):
        label = LongLabel(self.line_text)

        line = GLineEdit()
        line.setPlaceholderText(self.line_placeholder)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addWidget(line, 1)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.section_line = widget
        self.controls.line = line

    def draw_list(self):
        label = LongLabel(self.list_text)
        label.setFixedWidth(134)
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        list = GrowingTextEdit()
        list.setPlaceholderText(self.list_placeholder)

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
    modes = TaxonSelectMode
    mode_text = 'Taxon Selection'
    line_text = 'List of taxa (comma-separated) or other pattern that will be used as the qTaxa parameter of the active configuration:'
    list_text = (
        'Enter a list of taxa, separated by new lines. \n\n'
        'Combine taxa using the plus ("+") symbol.'
    )
    line_placeholder = 'ALL, >N, P:pattern, P+:pattern, Taxon1, Taxon2+Taxon3, ...'
    list_placeholder = 'Taxon1\nTaxon2+Taxon3\nTaxon4+Taxon5+Taxon6\n...'

    def __init__(self, parent=None):
        super().__init__(parent)

    def handleToggle(self, mode):
        self.controls.section_line.setVisible(mode == TaxonSelectMode.Line)
        self.controls.section_list.setVisible(mode == TaxonSelectMode.List)


class PairwiseSelector(ModeSelector):
    modes = PairwiseSelectMode
    mode_text = 'Pairwise Selection'
    line_text = (
        'List of taxon pairs (comma-separated) or other pattern that will be used as the qTaxa parameter of the active configuration. '
        'This is appended to any other qTaxa options from the taxon selection above.'
    )
    list_text = (
        'Enter a list of taxon pairs, joined with "VS", separated by new lines. \n\n'
        'Many pairs can be defined at once by using multiple "VS" in one line.'
    )
    line_placeholder = 'Taxon1VSALL, Taxon2VSTaxon3, Taxon4VSTaxon5VSTaxon6, ...'
    list_placeholder = 'Taxon1VSALL\nTaxon2VSTaxon3\nTaxon4VSTaxon5VSTaxon6\n...'

    def __init__(self, parent=None):
        super().__init__(parent)

    def handleToggle(self, mode):
        self.controls.section_line.setVisible(mode == PairwiseSelectMode.Line)
        self.controls.section_list.setVisible(mode == PairwiseSelectMode.List)


class TaxonRankSelector(Card):
    toggled = QtCore.Signal(TaxonRank)

    def __init__(self, parent=None):
        super().__init__(parent)

        title = 'Taxon rank:'
        desc = 'determines the maximum divergence that is allowed when simulating sequences.'
        label = QtWidgets.QLabel(
        f"""<html>
        <span style="font-size:16px;">{title}&nbsp;</span>
        <span style="font-size:12px;">{desc}</span>
        </html>""")

        group = RadioButtonGroup()
        group.valueChanged.connect(self.toggled)
        self.controls.rank = group

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(label)

        for rank in TaxonRank:
            button = RichRadioButton(rank.label, rank.description)
            layout.addWidget(button)
            group.add(button, rank)

        self.addLayout(layout)

    def setRank(self, rank):
        self.controls.rank.setValue(rank)


class GapsAsCharactersSelector(Card):
    toggled = QtCore.Signal(GapsAsCharacters)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel("Code alignment gaps as characters")
        label.setStyleSheet("""font-size: 16px;""")

        group = RadioButtonGroup()
        group.valueChanged.connect(self.toggled)
        self.controls.gaps = group

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(label)

        for mode in GapsAsCharacters:
            button = RichRadioButton(mode.label, mode.description)
            layout.addWidget(button)
            group.add(button, mode)

        self.addLayout(layout)

    def setMode(self, mode):
        self.controls.gaps.setValue(mode)


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
        self.cards.rank = TaxonRankSelector(self)
        self.cards.gaps = GapsAsCharactersSelector(self)

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

        self.binder.bind(self.cards.rank.toggled, object.properties.taxon_rank)
        self.binder.bind(object.properties.taxon_rank, self.cards.rank.setRank)

        self.binder.bind(self.cards.gaps.toggled, object.properties.gaps_as_characters)
        self.binder.bind(object.properties.gaps_as_characters, self.cards.gaps.setMode)

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
