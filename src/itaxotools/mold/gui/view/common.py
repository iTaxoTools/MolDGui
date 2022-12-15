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

from PySide6 import QtCore, QtGui, QtWidgets

from pathlib import Path

from itaxotools.common.utility import AttrDict, override

from .. import app
from ..model import Object
from ..utility import Guard, Binder
from ..types import Notification


class ObjectView(QtWidgets.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""ObjectView{background: Palette(Dark);}""")
        self.binder = Binder()
        self.object = None

    def setObject(self, object: Object):
        self.object = object
        self.binder.unbind_all()
        self.binder.bind(object.notification, self.showNotification)

    def showNotification(self, notification):
        icon = {
            Notification.Info: QtWidgets.QMessageBox.Information,
            Notification.Warn: QtWidgets.QMessageBox.Warning,
            Notification.Fail: QtWidgets.QMessageBox.Critical,
        }[notification.type]

        msgBox = QtWidgets.QMessageBox(self.window())
        msgBox.setWindowTitle(app.title)
        msgBox.setIcon(icon)
        msgBox.setText(notification.text)
        msgBox.setDetailedText(notification.info)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()

    def getOpenPath(self, caption ='Open File', dir=''):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), f'{app.title} - {caption}', dir)
        if not filename:
            return None
        return Path(filename)

    def getSavePath(self, caption ='Open File', dir=''):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window(), f'{app.title} - {caption}', dir)
        if not filename:
            return None
        return Path(filename)


class TaskView(ObjectView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""TaskView{background: Palette(Dark);}""")


class Card(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""Card{background: Palette(Midlight);}""")
        self.controls = AttrDict()

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(16, 8, 16, 8)
        self.setLayout(layout)

    def addWidget(self, widget):
        self.layout().addWidget(widget)

    def addLayout(self, widget):
        self.layout().addLayout(widget)

    @override
    def paintEvent(self, event):
        super().paintEvent(event)

        if self.layout().count():
            self.paintSeparators()

    def paintSeparators(self):
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        painter.setPen(option.palette.color(QtGui.QPalette.Mid))

        layout = self.layout()
        frame = layout.contentsRect()
        left = frame.left()
        right = frame.right()

        items = [
            item for item in (layout.itemAt(id) for id in range(0, layout.count()))
            if item.widget() and item.widget().isVisible()
            or item.layout()
        ]
        pairs = zip(items[:-1], items[1:])

        for first, second in pairs:
            bottom = first.geometry().bottom()
            top = second.geometry().top()
            middle = (bottom + top) / 2
            painter.drawLine(left, middle, right, middle)


class NoWheelComboBox(QtWidgets.QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class GLineEdit(QtWidgets.QLineEdit):

    textEditedSafe = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textEdited.connect(self._handleEdit)
        self._guard = Guard()

    def _handleEdit(self, text):
        with self._guard:
            self.textEditedSafe.emit(text)

    @override
    def setText(self, text):
        if self._guard:
            return
        super().setText(text)


class GSpinBox(QtWidgets.QSpinBox):

    valueChangedSafe = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valueChanged.connect(self._handleEdit)
        self._guard = Guard()

    def _handleEdit(self, value):
        with self._guard:
            self.valueChangedSafe.emit(value)

    @override
    def setValue(self, value):
        if self._guard:
            return
        super().setValue(value)

    @override
    def wheelEvent(self, event):
        event.ignore()
