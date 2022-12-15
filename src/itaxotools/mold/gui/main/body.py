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

from PySide6 import QtCore, QtWidgets

from .. import app
from ..types import Notification
from ..view import MoldView
from ..model import MoldModel
from ..utility import Binder

class ScrollArea(QtWidgets.QScrollArea):

    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setWidget(widget)


class Body(QtWidgets.QStackedWidget):
    """Mirrors Taxi3 logic"""

    def __init__(self, parent):
        super().__init__(parent)
        self.actions = parent.actions
        self.areas = dict()
        self.binder = Binder()

        self.addView(MoldModel, MoldView)

    def addView(self, object_type, view_type, *args, **kwargs):
        view = view_type(parent=self, *args, **kwargs)
        area = ScrollArea(view, self)
        self.areas[object_type] = area
        self.addWidget(area)

    def showModel(self, object: MoldModel):
        area = self.areas.get(type(object))
        view = area.widget()
        view.setObject(object)
        self.setCurrentWidget(area)
        area.ensureVisible(0, 0)

        self.binder.unbind_all()

        self.binder.bind(self.actions.open.triggered, view.open)
        self.binder.bind(self.actions.save.triggered, view.save)

        self.binder.bind(self.actions.start.triggered, object.start)
        self.binder.bind(self.actions.stop.triggered, object.stop)

        self.binder.bind(object.properties.ready, self.actions.start.setEnabled)
        self.binder.bind(object.properties.done, self.actions.save.setEnabled)
        self.binder.bind(object.properties.busy, self.actions.start.setVisible, lambda busy: not busy)
        self.binder.bind(object.properties.busy, self.actions.stop.setVisible)


        return True
