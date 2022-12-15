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

from itaxotools.common.utility import AttrDict, override
from itaxotools.common.widgets import VLineSeparator

from .common import Card, TaskView


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


class MoldView(TaskView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)

        layout = QtWidgets.QVBoxLayout()
        for card in self.cards:
            layout.addWidget(card)
        layout.addStretch(1)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
