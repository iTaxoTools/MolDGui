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
from collections import defaultdict

from itaxotools.common.utility import AttrDict, override
from itaxotools.common.widgets import VLineSeparator

from .. import app
from ..types import TaxonSelectMode, PairwiseSelectMode, TaxonRank, ScoringThreshold, GapsAsCharacters, AdvancedMDNCProperties, AdvancedRDNSProperties, ConfigurationMode
from ..files import is_fasta
from ..utility import type_convert
from .common import Card, TaskView, GLineEdit, GTextEdit, NoWheelComboBox, NoWheelRadioButton, LongLabel, RadioButtonGroup, RichRadioButton, SpinningCircle, CategoryButton


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


class TextEditLogger(QtWidgets.QPlainTextEdit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.scrollbarOldValue = 0
        self.scrollbarAtBottom = True
        self.scrollbarAtTop = True
        self.scrollbarLock = True
        self.scrollbarLockTimer = QtCore.QTimer()
        self.scrollbarLockTimer.timeout.connect(self.scrollbarUnlock)
        self.scrollbarLockTimer.setSingleShot(True)
        self.verticalScrollBar().valueChanged.connect(self.checkScrollbar)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if self.scrollbarAtBottom or self.scrollbarAtTop:
            if not self.scrollbarLockTimer.isActive():
                self.scrollbarLockTimer.start(300)
            if self.scrollbarLock:
                # Consume event, so parent doesn't scroll
                event.accept()
        else:
            self.scrollbarLock = True

    def scrollbarUnlock(self):
        self.scrollbarLock = False

    def append(self, text):
        self.moveCursor(QtGui.QTextCursor.End)
        self.insertPlainText(text)
        self.moveCursor(QtGui.QTextCursor.End)

        if not self.scrollbarAtBottom:
            self.verticalScrollBar().setValue(self.scrollbarOldValue)

    def checkScrollbar(self, value):
        scrollbar = self.verticalScrollBar()
        self.scrollbarOldValue = value
        self.scrollbarAtBottom = scrollbar.value() == scrollbar.maximum()
        self.scrollbarAtTop = scrollbar.value() == 0


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
        homepage = QtWidgets.QPushButton('Homepage')
        galaxy = QtWidgets.QPushButton('Galaxy')
        itaxotools = QtWidgets.QPushButton('iTaxoTools')
        itaxotools.setFixedWidth(100)

        manual.clicked.connect(self.openManual)
        homepage.clicked.connect(self.openHomepage)
        galaxy.clicked.connect(self.openGalaxy)
        itaxotools.clicked.connect(self.openItaxotools)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(manual)
        buttons.addWidget(homepage)
        buttons.addWidget(galaxy)
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

    def openManual(self):
        url = QtCore.QUrl.fromLocalFile(str(app.resources.docs.manual))
        QtGui.QDesktopServices.openUrl(url)

    def openHomepage(self):
        QtGui.QDesktopServices.openUrl(app.homepage_url)

    def openGalaxy(self):
        QtGui.QDesktopServices.openUrl(app.galaxy_url)

    def openItaxotools(self):
        QtGui.QDesktopServices.openUrl(app.itaxotools_url)


class ProgressCard(Card):

    def __init__(self, parent):
        super().__init__(parent)
        self._success = False
        self._busy = False

        check = QtWidgets.QLabel('\u2714')
        check.setStyleSheet("""font-size: 16px; color: Palette(Shadow);""")

        cross = QtWidgets.QLabel('\u2718')
        cross.setStyleSheet("""font-size: 16px; color: Palette(Shadow);""")

        spin = SpinningCircle()
        spin.radius = 7

        wait = QtWidgets.QLabel('Diagnosing sequences, please hold on...')
        wait.setStyleSheet("""font-size: 16px;""")

        done = QtWidgets.QLabel('Progress Logs')
        done.setStyleSheet("""font-size: 16px;""")

        details = QtWidgets.QPushButton('Details')
        details.setCheckable(True)
        details.setChecked(True)

        head = QtWidgets.QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(12)
        head.addWidget(spin)
        head.addWidget(check)
        head.addWidget(cross)
        head.addWidget(wait, 1)
        head.addWidget(done, 1)
        head.addWidget(details)

        bar = QtWidgets.QProgressBar()
        bar.setMaximum(0)
        bar.setMinimum(0)
        bar.setValue(0)
        bar.setVisible(False)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(8)
        layout.addLayout(head)
        layout.addWidget(bar)

        logger = TextEditLogger()

        self.addLayout(layout)
        self.addWidget(logger)

        details.toggled.connect(logger.setVisible)

        self.controls.check = check
        self.controls.cross = cross
        self.controls.spin = spin
        self.controls.wait = wait
        self.controls.done = done
        self.controls.details = details
        self.controls.bar = bar
        self.controls.logger = logger

    def setBusy(self, busy):
        self._busy = busy
        self.controls.done.setVisible(not busy)
        self.controls.spin.setVisible(busy)
        self.controls.wait.setVisible(busy)
        self.controls.details.setChecked(busy)
        # self.controls.bar.setVisible(busy)
        self.updateBadge()

    def setSuccess(self, success):
        self._success = success
        self.updateBadge()

    def updateBadge(self):
        self.controls.check.setVisible(not self._busy and self._success)
        self.controls.cross.setVisible(not self._busy and not self._success)


class ConfigSelector(Card):
    browse = QtCore.Signal()

    modes = ConfigurationMode
    mode_text = 'Set parameters'
    label_text = 'Configuration File'
    placeholder_text = 'Load all parameters from a configuration file'
    warning_text = (
        '<b>Warning:</b> loading a configuration file will overwrite all fields below. '
        'It is then possible to modify the loaded parameters.'
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_modes()
        self.draw_selector()
        self.controls.mode.setValue(self.modes.Fields)

    def draw_modes(self):
        label = QtWidgets.QLabel(self.mode_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setFixedWidth(134)

        group = RadioButtonGroup()
        group.valueChanged.connect(self.handleToggle)
        self.controls.mode = group

        radios = QtWidgets.QHBoxLayout()
        radios.setContentsMargins(0, 0, 0, 0)
        radios.setSpacing(16)
        for mode in self.modes:
            button = NoWheelRadioButton(str(mode))
            radios.addWidget(button)
            group.add(button, mode)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(32)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(radios, 3)
        layout.addStretch(1)
        layout.addSpacing(32)
        self.addLayout(layout)

    def draw_selector(self):
        label = QtWidgets.QLabel(self.label_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setFixedWidth(134)

        filename = GLineEdit()
        filename.setReadOnly(True)
        filename.setPlaceholderText(self.placeholder_text)
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

        head = QtWidgets.QHBoxLayout()
        head.setSpacing(16)
        head.addWidget(label)
        head.addSpacing(24)
        head.addWidget(filename, 1)
        head.addWidget(browse)

        warning = LongLabel(self.warning_text)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addLayout(head)
        layout.addWidget(warning)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.selector = widget
        self.controls.filename = filename
        self.controls.browse = browse

    def handleToggle(self, mode):
        self.controls.selector.setVisible(mode.has_file)

    def setPath(self, path):
        if path is None:
            self.controls.filename.setText('')
            self.controls.mode.setValue(self.modes.Fields)
        else:
            self.controls.filename.setText(str(path))
            self.controls.mode.setValue(self.modes.File)


class SequenceSelector(Card):
    browse = QtCore.Signal()
    label_text = 'Sequence Data File'
    placeholder_text = 'Select a Fasta file that includes taxon identifiers'

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel(self.label_text + ':')
        label.setStyleSheet("""font-size: 16px;""")
        label.setFixedWidth(134)

        filename = GLineEdit()
        filename.setReadOnly(True)
        filename.setPlaceholderText(self.placeholder_text)
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
        layout.setSpacing(16)
        layout.addWidget(label)
        layout.addSpacing(24)
        layout.addWidget(filename, 1)
        layout.addWidget(browse)
        self.addLayout(layout)

        self.controls.filename = filename
        self.controls.browse = browse

    def setPath(self, path):
        if path is None:
            self.controls.filename.setText('')
        else:
            self.controls.filename.setText(str(path))


class ModeSelector(Card):
    toggled = QtCore.Signal(object)

    modes = []
    mode_text = 'Mode Selection'
    list_text = 'List text.'
    list_placeholder = 'List placeholder...'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_modes()
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
            button = NoWheelRadioButton(str(mode))
            radios.addWidget(button)
            group.add(button, mode)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(32)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(radios, 3)
        layout.addStretch(1)
        layout.addSpacing(32)
        self.addLayout(layout)

    def draw_list(self):
        label = LongLabel(self.list_text)

        list = GrowingTextEdit()
        list.setPlaceholderText(self.list_placeholder)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
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
        self.controls.section_list.setVisible(True)


class TaxonSelector(ModeSelector):
    modes = TaxonSelectMode
    mode_text = 'Taxon Selection'
    list_text = (
        'Please enter a list of taxa for diagnosis, separated by commas or new lines. '
        'You may merge many taxa together as one by using the "+" symbol. '
        'They will be used as the qTaxa parameter of the active configuration. '
        'Also accepts any other patterns mentioned in the manual, such as '
        '">N", "P:pattern", "P+:pattern" and "ALL".'
    )
    list_placeholder = (
        'ALL, >N, P:pattern, P+:pattern, Taxon1, Taxon2 + Taxon3, ...\n'
        'Taxon4 + Taxon5 + Taxon6\n...'
    )

    def __init__(self, parent=None):
        super().__init__(parent)

    def handleToggle(self, mode):
        self.controls.section_list.setVisible(mode == TaxonSelectMode.List)


class PairwiseSelector(ModeSelector):
    modes = PairwiseSelectMode
    mode_text = 'Pairwise Selection'
    list_text = (
        'Please enter a list of taxon combinations, separated by commas or new lines. '
        'Combinations are defined using two or more taxon names, joined by "VS". '
        'This is appended to any other qTaxa options from the taxon selection above.'
    )
    list_placeholder = (
        'Taxon1 VS ALL, Taxon2 VS Taxon3, ...\n'
        'Taxon4 VS Taxon5 VS Taxon6\n...'
    )

    def __init__(self, parent=None):
        super().__init__(parent)

    def handleToggle(self, mode):
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


class ExpandableCard(Card):
    title = 'Expandable Card'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw_title()
        self.draw_contents()

        self.controls.title.toggled.connect(self.handleToggled)

        self.controls.title.setChecked(False)
        self.controls.contents.setVisible(False)

    def draw_title(self):
        title = CategoryButton(self.title)
        title.setStyleSheet("""font-size: 16px;""")
        self.addWidget(title)

        self.controls.title = title

    def draw_contents(self):
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.contents = widget

    def handleToggled(self, checked):
        self.controls.contents.setVisible(checked)
        QtCore.QTimer.singleShot(10, self.update)

    def setContentsEnabled(self, enable):
        self.controls.contents.setEnabled(enable)


class ExpandableEnumCard(ExpandableCard):
    title = 'Expandable Enum Card'
    enum = []
    widget_types = defaultdict(lambda: GLineEdit)

    def draw_contents(self):
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setColumnStretch(2, 1)
        layout.setSpacing(16)

        for row, entry in enumerate(self.enum):
            label = QtWidgets.QLabel(f'<b>{entry.label}:</b>')
            widget_type = self.widget_types[entry]
            edit = widget_type()
            edit.setFixedWidth(100)
            description = QtWidgets.QLabel(f'{entry.description}.')
            layout.addWidget(label, row, 0)
            layout.addWidget(edit, row, 1)
            layout.addWidget(description, row, 2)
            self.controls[entry.key] = edit

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.addWidget(widget)

        self.controls.contents = widget


class MDNCSelector(ExpandableEnumCard):
    title = 'Advanced parameters for mDNC recovery'
    enum = AdvancedMDNCProperties


class ScoringCombobox(NoWheelComboBox):
    valueChanged = QtCore.Signal(ScoringThreshold)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for threshold in ScoringThreshold:
            self.addItem(threshold.label, threshold.value)
        self.currentIndexChanged.connect(self.handleIndexChanged)

    def handleIndexChanged(self, index):
        data = self.itemData(index, QtCore.Qt.UserRole)
        value = ScoringThreshold(data)
        self.valueChanged.emit(value)

    def setValue(self, value):
        index = self.findData(value, QtCore.Qt.UserRole)
        self.setCurrentIndex(index)


class PdiffEdit(GLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText('From taxon rank')


class RDNSSelector(ExpandableEnumCard):
    title = 'Parameters of artificial datasets (only rDNSs)'
    enum = AdvancedRDNSProperties
    widget_types = defaultdict(lambda: GLineEdit, {
        enum.Pdiff: PdiffEdit,
        enum.Scoring: ScoringCombobox,
    })


class ResultViewer(Card):
    view = QtCore.Signal(str, Path)
    save = QtCore.Signal(str, Path)

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.text = label_text
        self.path = None

        label = QtWidgets.QLabel(label_text)
        label.setStyleSheet("""font-size: 16px;""")

        check = QtWidgets.QLabel('\u2714')
        check.setStyleSheet("""font-size: 16px; color: Palette(Shadow);""")

        save = QtWidgets.QPushButton('Save')
        save.clicked.connect(self.handleSave)

        view = QtWidgets.QPushButton('View')
        view.clicked.connect(self.handleView)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(check)
        layout.addSpacing(12)
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(save)
        layout.addSpacing(16)
        layout.addWidget(view)
        self.addLayout(layout)

        self.controls.view = view
        self.controls.save = save

    def setPath(self, path):
        self.path = path
        self.setVisible(path is not None)

    def handleView(self):
        self.view.emit(self.text, self.path)

    def handleSave(self):
        self.save.emit(self.text, self.path)


class ResultDialog(QtWidgets.QDialog):
    save = QtCore.Signal(Path)

    def __init__(self, text, path, parent):
        super().__init__(parent)
        self.path = path

        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(app.title + ' - ' + text)
        self.resize(460, 680)
        self.setModal(True)

        viewer = QtWidgets.QTextBrowser()
        # viewer.setStyleSheet("""QTextBrowser{margin: 12px;}""")
        with open(path) as file:
            viewer.setHtml(file.read())

        save = QtWidgets.QPushButton('Save')
        save.clicked.connect(self.handleSave)

        close = QtWidgets.QPushButton('Close')
        close.clicked.connect(self.reject)
        close.setDefault(True)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(save)
        buttons.addWidget(close)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(viewer)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def handleSave(self):
        self.save.emit(self.path)


class DiagnosisViewer(ResultViewer):
    def __init__(self, parent=None):
        super().__init__('Molecular Diagnosis', parent)


class PairwiseViewer(ResultViewer):
    def __init__(self, parent=None):
        super().__init__('Pairwise Analysis', parent)


class MoldView(TaskView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.draw()

    def draw(self):
        self.cards = AttrDict()
        self.cards.title = TitleCard(self)
        self.cards.diagnosis = DiagnosisViewer(self)
        self.cards.pairwise = PairwiseViewer(self)
        self.cards.progress = ProgressCard(self)
        self.cards.configuration = ConfigSelector(self)
        self.cards.sequence = SequenceSelector(self)
        self.cards.taxa = TaxonSelector(self)
        self.cards.pairs = PairwiseSelector(self)
        self.cards.rank = TaxonRankSelector(self)
        self.cards.gaps = GapsAsCharactersSelector(self)
        self.cards.mdnc = MDNCSelector(self)
        self.cards.rdns = RDNSSelector(self)

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

        for card in [
            self.cards.configuration,
            self.cards.sequence,
            self.cards.taxa,
            self.cards.pairs,
            self.cards.rank,
            self.cards.gaps,
        ]:
            self.binder.bind(object.properties.editable, card.setEnabled)

        for card in [
            self.cards.mdnc,
            self.cards.rdns,
        ]:
            self.binder.bind(object.properties.editable, card.setContentsEnabled)
            self.binder.bind(object.properties.editable, card.controls.title.setGray, lambda x: not x)

        self.binder.bind(object.properties.busy, self.cards.progress.setBusy)
        self.binder.bind(object.properties.has_logs, self.cards.progress.setVisible)
        self.binder.bind(object.properties.done, self.cards.progress.setSuccess)

        self.binder.bind(object.lineLogged, self.cards.progress.controls.logger.append)
        self.binder.bind(object.clearLogs, self.handleClearLogs)
        self.binder.bind(object.notification, self.showNotification)
        # self.bind(object.progression, self.cards.progress.showProgress)

        # self.binder.bind(object.properties.configuration_path, self.cards.configuration.setVisible, lambda path: path is not None)
        self.binder.bind(object.properties.configuration_path, self.cards.configuration.setPath)
        self.binder.bind(object.properties.sequence_path, self.cards.sequence.setPath)
        self.binder.bind(object.properties.configuration_path, self.updateWindowTitle)
        self.binder.bind(object.properties.sequence_path, self.updateWindowTitle)

        self.binder.bind(self.cards.taxa.toggled, object.properties.taxon_mode)
        self.binder.bind(object.properties.taxon_mode, self.cards.taxa.setMode)
        self.binder.bind(self.cards.taxa.controls.list.textEditedSafe, object.properties.taxon_list)
        self.binder.bind(object.properties.taxon_list, self.cards.taxa.controls.list.setText)

        self.binder.bind(self.cards.pairs.toggled, object.properties.pairs_mode)
        self.binder.bind(object.properties.pairs_mode, self.cards.pairs.setMode)
        self.binder.bind(self.cards.pairs.controls.list.textEditedSafe, object.properties.pairs_list)
        self.binder.bind(object.properties.pairs_list, self.cards.pairs.controls.list.setText)

        self.binder.bind(self.cards.rank.toggled, object.properties.taxon_rank)
        self.binder.bind(object.properties.taxon_rank, self.cards.rank.setRank)

        self.binder.bind(self.cards.gaps.toggled, object.properties.gaps_as_characters)
        self.binder.bind(object.properties.gaps_as_characters, self.cards.gaps.setMode)

        self.binder.bind(self.cards.mdnc.controls.cutoff.textEditedSafe, object.mdnc.properties.cutoff)
        self.binder.bind(object.mdnc.properties.cutoff, self.cards.mdnc.controls.cutoff.setText)

        self.binder.bind(self.cards.mdnc.controls.nucleotides.textEditedSafe, object.mdnc.properties.nucleotides, lambda x: type_convert(x, int, None))
        self.binder.bind(object.mdnc.properties.nucleotides, self.cards.mdnc.controls.nucleotides.setText, lambda x: str(x) if x is not None else '')

        self.binder.bind(self.cards.mdnc.controls.iterations.textEditedSafe, object.mdnc.properties.iterations, lambda x: type_convert(x, int, None))
        self.binder.bind(object.mdnc.properties.iterations, self.cards.mdnc.controls.iterations.setText, lambda x: str(x) if x is not None else '')

        self.binder.bind(self.cards.mdnc.controls.max_length_raw.textEditedSafe, object.mdnc.properties.max_length_raw, lambda x: type_convert(x, int, None))
        self.binder.bind(object.mdnc.properties.max_length_raw, self.cards.mdnc.controls.max_length_raw.setText, lambda x: str(x) if x is not None else '')

        self.binder.bind(self.cards.mdnc.controls.max_length_refined.textEditedSafe, object.mdnc.properties.max_length_refined, lambda x: type_convert(x, int, None))
        self.binder.bind(object.mdnc.properties.max_length_refined, self.cards.mdnc.controls.max_length_refined.setText, lambda x: str(x) if x is not None else '')

        self.binder.bind(self.cards.mdnc.controls.indexing_reference.textEditedSafe, object.mdnc.properties.indexing_reference)
        self.binder.bind(object.mdnc.properties.indexing_reference, self.cards.mdnc.controls.indexing_reference.setText)

        self.binder.bind(self.cards.rdns.controls.p_diff.textEditedSafe, object.rdns.properties.p_diff, lambda x: type_convert(x, int, None))
        self.binder.bind(object.rdns.properties.p_diff, self.cards.rdns.controls.p_diff.setText, lambda x: str(x) if x is not None else '')

        self.binder.bind(self.cards.rdns.controls.n_max.textEditedSafe, object.rdns.properties.n_max, lambda x: type_convert(x, int, None))
        self.binder.bind(object.rdns.properties.n_max, self.cards.rdns.controls.n_max.setText, lambda x: str(x) if x is not None else '')

        self.binder.bind(self.cards.rdns.controls.scoring.valueChanged, object.rdns.properties.scoring)
        self.binder.bind(object.rdns.properties.scoring, self.cards.rdns.controls.scoring.setValue)

        self.binder.bind(object.properties.result_diagnosis, self.cards.diagnosis.setPath)
        self.binder.bind(object.properties.result_pairwise, self.cards.pairwise.setPath)

        self.binder.bind(self.cards.diagnosis.view, self.viewDiagnosis)
        self.binder.bind(self.cards.diagnosis.save, self.saveDiagnosis)
        self.binder.bind(self.cards.pairwise.view, self.viewPairwise)
        self.binder.bind(self.cards.pairwise.save, self.savePairwise)

    def updateWindowTitle(self):
        if self.object.configuration_path:
            filename = self.object.configuration_path.name
        elif self.object.sequence_path:
            filename = self.object.sequence_path.name
        else:
            filename = None

        title = f'{app.title} - {filename}' if filename else app.title
        self.window().setWindowTitle(title)

    def handleClearLogs(self):
        self.cards.progress.controls.logger.clear()
        self.parent().parent().verticalScrollBar().setValue(0)

    def open(self):
        path = self.getOpenPath('Open sequences or configuration file')
        if path is None:
            return
        if is_fasta(path):
            self.object.open_sequence_path(path)
        else:
            self.object.open_configuration_path(path)

    def openConfiguration(self):
        path = self.getOpenPath('Open configuration file', filter='MolD Configuration (*.*)')
        if path is not None:
            self.object.open_configuration_path(path)

    def openSequence(self):
        path = self.getOpenPath('Open sequence file', filter='Fasta Sequences (*.*)')
        if path is not None:
            self.object.open_sequence_path(path)

    def viewDiagnosis(self, text, path):
        dialog = ResultDialog(text, path, self.window())
        dialog.save.connect(self.saveDiagnosis)
        self.window().msgShow(dialog)

    def viewPairwise(self, text, path):
        dialog = ResultDialog(text, path, self.window())
        dialog.save.connect(self.savePairwise)
        self.window().msgShow(dialog)

    def saveDiagnosis(self):
        path = self.getSavePath('Save Molecular Diagnosis', str(self.object.suggested_diagnosis))
        if path:
            self.object.save_diagnosis(path)

    def savePairwise(self):
        path = self.getSavePath('Save Pairwise Analysis', str(self.object.suggested_pairwise))
        if path:
            self.object.save_pairwise(path)

    def save(self):
        path = self.getExistingDirectory('Save All', str(self.object.suggested_directory))
        if path:
            self.object.save_all(path)

    def start(self):
        self.object.start()

    def stop(self):
        if self.getConfirmation('Stop diagnosis', 'Are you sure you want to stop the ongoing diagnosis?'):
            self.object.stop()

    def clear(self):
        if self.getConfirmation('Clear results', 'Are you sure you want to clear all results and try again?'):
            self.object.clear()
