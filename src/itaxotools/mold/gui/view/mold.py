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
from .common import Card, TaskView, GLineEdit


def is_fasta(path):
    with open(path) as file:
        char = file.read(1)
        return char == '>'


class TitleCard(Card):
    run = QtCore.Signal()
    cancel = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        description = QtWidgets.QLabel(
            'Identify diagnostic nucleotide combinations (DNCs) in DNA sequence alignments, which can be used to provide formal diagnoses of these taxa. This is in the form of "redundant DNC” (rDNC), which takes into account unsampled genetic diversity.')
        description.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        description.setWordWrap(True)

        citations = QtWidgets.QLabel(
            'Fedosov A.E., Achaz G., Gontchar A., Puillandre N. 2022. MOLD, a novel software to compile accurate and reliable DNA diagnoses for taxonomic descriptions. Molecular Ecology Resources, DOI: 10.1111/1755-0998.13590.')
        citations.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        citations.setStyleSheet("color: Palette(Dark)")
        citations.setWordWrap(True)

        contents = QtWidgets.QVBoxLayout()
        contents.addWidget(description)
        contents.addWidget(citations)
        contents.addStretch(1)
        contents.setSpacing(12)

        manual = QtWidgets.QPushButton('Manual')
        galaxy = QtWidgets.QPushButton('Galaxy')
        homepage = QtWidgets.QPushButton('Homepage')
        itaxotools = QtWidgets.QPushButton('iTaxoTools')
        itaxotools.setMinimumWidth(100)

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
        # self.bindings = set()
        # self.guard = Guard()

        label = QtWidgets.QLabel(label_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setMinimumWidth(174)

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
        super().__init__('Sequence Data File', 'Open a Fasta file that includes taxon identifiers', parent)


class MoldView(TaskView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.configuration = ConfigSelector(self)
        self.cards.sequence = SequenceSelector(self)

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

        self.binder.bind(object.notification, self.showNotification)
        # self.bind(object.progression, self.cards.progress.showProgress)

        self.binder.bind(object.properties.configuration_path, self.cards.configuration.setVisible, lambda path: path is not None)
        self.binder.bind(object.properties.configuration_path, self.cards.configuration.setPath)
        self.binder.bind(object.properties.sequence_path, self.cards.sequence.setPath)

        self.binder.bind(self.cards.configuration.browse, self.openConfiguration)
        self.binder.bind(self.cards.sequence.browse, self.openSequence)

    def open(self):
        path = self.getOpenPath()
        if path is None:
            return
        if is_fasta(path):
            self.object.open_sequences(path)
        else:
            self.object.open_configuration(path)

    def openConfiguration(self):
        path = self.getOpenPath()
        self.object.open_configuration(path)

    def openSequence(self):
        path = self.getOpenPath()
        self.object.open_sequence(path)

    def save(self):
        path = self.getSavePath('Save all')
        self.object.save(path)
