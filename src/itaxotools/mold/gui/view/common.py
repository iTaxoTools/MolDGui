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

    def getOpenPath(self, caption ='Open File', dir='', filter=''):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), f'{app.title} - {caption}', dir, filter=filter)
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
        layout.setContentsMargins(16, 10, 16, 10)
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


class GTextEdit(QtWidgets.QPlainTextEdit):

    textEditedSafe = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self._handleEdit)
        self._guard = Guard()

    def _handleEdit(self):
        with self._guard:
            self.textEditedSafe.emit(self.toPlainText())

    @override
    def setText(self, text):
        if self._guard:
            return
        super().setPlainText(text)


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


class LongLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.setWordWrap(True)

        action = QtGui.QAction('&Copy', self)
        action.triggered.connect(self.copy)
        self.addAction(action)

        action = QtGui.QAction(self)
        action.setSeparator(True)
        self.addAction(action)

        action = QtGui.QAction('Select &All', self)
        action.triggered.connect(self.select)
        self.addAction(action)

    def copy(self):
        text = self.selectedText()
        QtWidgets.QApplication.clipboard().setText(text)

    def select(self):
        self.setSelection(0, len(self.text()))


class RadioButtonGroup(QtCore.QObject):
    valueChanged = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.members = dict()
        self.value = None

    def add(self, widget, value):
        self.members[widget] = value
        widget.toggled.connect(self.handleToggle)

    def handleToggle(self, checked):
        if not checked:
            return
        self.value = self.members[self.sender()]
        self.valueChanged.emit(self.value)

    def setValue(self, newValue):
        self.value = newValue
        for widget, value in self.members.items():
            widget.setChecked(value == newValue)

class RichRadioButton(QtWidgets.QRadioButton):
    def __init__(self, text, desc, parent=None):
        super().__init__(text, parent)
        self.desc = desc
        self.setStyleSheet("""
            RichRadioButton {
                letter-spacing: 1px;
                font-weight: bold;
            }""")
        font = self.font()
        font.setBold(False)
        font.setLetterSpacing(QtGui.QFont.PercentageSpacing, 0)
        self.small_font = font

    def event(self, event):
        if isinstance(event, QtGui.QWheelEvent):
            # Fix scrolling when hovering disabled button
            event.ignore()
            return False
        return super().event(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        painter.setFont(self.small_font)
        width = self.size().width()
        height = self.size().height()
        sofar = super().sizeHint().width()

        rect = QtCore.QRect(sofar, 0, width - sofar, height)
        flags = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        painter.drawText(rect, flags, self.desc)

        painter.end()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        x = event.localPos().x()
        w = self.sizeHint().width()
        if x < w:
            self.setChecked(True)

    def sizeHint(self):
        metrics = QtGui.QFontMetrics(self.small_font)
        extra = metrics.horizontalAdvance(self.desc)
        size = super().sizeHint()
        size += QtCore.QSize(extra, 0)
        return size
