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
from ..utility import PropertyObject, Property
from .body import Body
from .footer import Footer
from .header import Header


class MainState(PropertyObject):
    dirty_data = Property(bool, False)


class Main(ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, files=[]):
        super(Main, self).__init__(parent)

        self.title = app.title
        self.setWindowIcon(app.resources.icons.app)
        self.setWindowTitle(app.title)
        self.resize(700, 560)

        self.act()
        self.draw()

        self.state = MainState()
        self.model = MoldModel('Molecular diagnosis')
        self.widgets.body.showModel(self.model)

        for path in (Path(file) for file in files):
            if is_fasta(path):
                self.model.open_sequence_path(path)
            else:
                self.model.open_configuration_path(path)

    def act(self):
        """Populate dialog actions"""
        self.actions = AttrDict()

        action = QtGui.QAction('&Open', self)
        action.setIcon(app.resources.icons.open)
        action.setShortcut(QtGui.QKeySequence.Open)
        action.setStatusTip('Open an existing file')
        self.actions.open = action

        self.actions.open_sequences = QtGui.QAction('Sequence data file', self)
        self.actions.open_configuration = QtGui.QAction('Configuration file', self)

        action = QtGui.QAction('&Save all', self)
        action.setIcon(app.resources.icons.save)
        action.setShortcut(QtGui.QKeySequence.Save)
        action.setStatusTip('Save results')
        self.actions.save = action

        action = QtGui.QAction('&Run', self)
        action.setIcon(app.resources.icons.run)
        action.setShortcut('Ctrl+R')
        action.setStatusTip('Run MolD')
        self.actions.start = action

        action = QtGui.QAction('S&top', self)
        action.setIcon(app.resources.icons.stop)
        action.setShortcut(QtGui.QKeySequence.Cancel)
        action.setStatusTip('Stop MolD')
        action.setVisible(False)
        self.actions.stop = action

        action = QtGui.QAction('Cl&ear', self)
        action.setIcon(app.resources.icons.clear)
        action.setShortcut('Ctrl+E')
        action.setStatusTip('Stop MolD')
        action.setVisible(False)
        self.actions.clear = action

    def draw(self):
        """Draw all contents"""
        self.widgets = AttrDict()
        self.widgets.header = Header(self)
        self.widgets.body = Body(self)
        self.widgets.footer = Footer(self)

        openButton = QtWidgets.QToolButton(self)
        openButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        openButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        openMenu = QtWidgets.QMenu(openButton)
        openMenu.setStyleSheet("""
            QMenu { border: 1px solid palette(Mid); }
            QMenu::item { padding: 6px 24px 6px 16px; }
            QMenu::item:selected  { background: Palette(Highlight); color: Palette(Window) }
        """)
        openMenu.addAction(self.actions.open_sequences)
        openMenu.addAction(self.actions.open_configuration)
        openButton.setDefaultAction(self.actions.open)
        openButton.setMenu(openMenu)

        self.widgets.header.toolBar.addWidget(openButton)
        self.widgets.header.toolBar.addAction(self.actions.save)
        self.widgets.header.toolBar.addAction(self.actions.start)
        self.widgets.header.toolBar.addAction(self.actions.stop)
        self.widgets.header.toolBar.addAction(self.actions.clear)


        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widgets.header)
        layout.addWidget(self.widgets.body, 1)
        layout.addWidget(self.widgets.footer)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def reject(self):
        if self.state.dirty_data:
            return super().reject()
        return True
