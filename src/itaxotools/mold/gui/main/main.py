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

"""Main dialog window"""

from PySide6 import QtCore, QtGui, QtWidgets

import shutil
from pathlib import Path

from itaxotools.common.utility import AttrDict
from itaxotools.common.widgets import ToolDialog

from .. import app
from ..model import MoldModel
from ..files import is_fasta
from .body import Body
from .footer import Footer
from .header import Header


class Main(ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, files=[]):
        super(Main, self).__init__(parent)

        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowIcon(app.resources.icons.app)
        self.setWindowTitle(app.title)
        self.resize(700, 560)

        self.act()
        self.draw()

        self.model = MoldModel('Molecular Diagnosis')
        self.widgets.body.showModel(self.model)

        for path in (Path(file) for file in files):
            if is_fasta(path):
                self.model.open_sequence_path(path)
            else:
                self.model.open_configuration_path(path)

    def act(self):
        """Populate dialog actions"""
        self.actions = AttrDict()

        self.actions.open = QtGui.QAction('&Open', self)
        self.actions.open.setIcon(app.resources.icons.open)
        self.actions.open.setShortcut(QtGui.QKeySequence.Open)
        self.actions.open.setStatusTip('Open an existing file')

        self.actions.save = QtGui.QAction('&Save all', self)
        self.actions.save.setIcon(app.resources.icons.save)
        self.actions.save.setShortcut(QtGui.QKeySequence.Save)
        self.actions.save.setStatusTip('Save results')

        self.actions.start = QtGui.QAction('&Run', self)
        self.actions.start.setIcon(app.resources.icons.run)
        self.actions.start.setShortcut('Ctrl+R')
        self.actions.start.setStatusTip('Run MolD')

        self.actions.stop = QtGui.QAction('&Stop', self)
        self.actions.stop.setIcon(app.resources.icons.stop)
        self.actions.stop.setStatusTip('Stop MolD')
        self.actions.stop.setVisible(False)

    def draw(self):
        """Draw all contents"""
        self.widgets = AttrDict()
        self.widgets.header = Header(self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

        for action in self.actions:
            self.widgets.header.toolBar.addAction(action)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widgets.header)
        layout.addWidget(self.widgets.body, 1)
        layout.addWidget(self.widgets.footer)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
