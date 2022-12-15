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
        self.resize(600, 500)

        self.draw()
        self.act()

        self.model = MoldModel()
        self.widgets.body.showModel(self.model)

        for file in files:
            print(file)

    def draw(self):
        """Draw all contents"""
        self.widgets = AttrDict()
        self.widgets.header = Header(self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widgets.header)
        layout.addWidget(self.widgets.body, 1)
        layout.addWidget(self.widgets.footer)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def act(self):
        """Populate dialog actions"""
        self.actions = AttrDict()

        self.actions.open = QtGui.QAction('&Open', self)
        self.actions.open.setIcon(app.resources.icons.open)
        self.actions.open.setShortcut(QtGui.QKeySequence.Open)
        self.actions.open.setStatusTip('Open an existing file')
        self.actions.open.triggered.connect(self.handleOpen)

        self.actions.save = QtGui.QAction('&Save', self)
        self.actions.save.setIcon(app.resources.icons.save)
        self.actions.save.setShortcut(QtGui.QKeySequence.Save)
        self.actions.save.setStatusTip('Save results')
        self.actions.save.triggered.connect(self.handleSave)

        self.actions.run = QtGui.QAction('&Run', self)
        self.actions.run.setIcon(app.resources.icons.run)
        self.actions.run.setShortcut('Ctrl+R')
        self.actions.run.setStatusTip('Run MolD')
        self.actions.run.triggered.connect(self.handleRun)

        self.actions.stop = QtGui.QAction('&Stop', self)
        self.actions.stop.setIcon(app.resources.icons.stop)
        self.actions.stop.setStatusTip('Stop MolD')
        self.actions.stop.triggered.connect(self.handleStop)
        self.actions.stop.setVisible(False)

        self.widgets.header.toolBar.addAction(self.actions.open)
        self.widgets.header.toolBar.addAction(self.actions.save)
        self.widgets.header.toolBar.addAction(self.actions.run)
        self.widgets.header.toolBar.addAction(self.actions.stop)

    def handleOpen(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, f'{app.title} - Open File')
        if not filename:
            return
        print(filename)

    def handleSave(self):
        try:
            self._handleSave()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, app.title, str(exception))

    def _handleSave(self):
        print('save')

    def handleRun(self):
        print('run')

    def handleStop(self):
        print('stop')
