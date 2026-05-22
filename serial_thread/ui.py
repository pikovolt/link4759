# coding: utf-8
from __future__ import annotations

import sys

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .commands import CommandKind, CommandRequest, CommandResult
from .dir_item import DirList, DirItem
from .serial_worker import SerialWorker


class Form(QDialog):
    """PySide2 UI.

    Design rule:
        This class never touches serial.Serial.
        It only sends CommandRequest objects to SerialWorker.
    """

    request_command = QtCore.Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("link 4759Player - threaded sample")

        self._dirlist = DirList()

        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)

        self.btnConnect = QPushButton("connect")
        self.btnDisconnect = QPushButton("disconnect")
        self.btnDir = QPushButton("get dir")
        self.btnCd = QPushButton("change dir")
        self.btnPlay = QPushButton("play")
        self.btnStop = QPushButton("stop")
        self.btnHelp = QPushButton("help")
        self.btnSend = QPushButton("send")

        self._build_layout()
        self._wire_ui()

        self.thread = QtCore.QThread(self)
        self.worker = SerialWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start)
        self.request_command.connect(self.worker.enqueue)

        self.worker.connected.connect(self.on_connected)
        self.worker.disconnected.connect(self.on_disconnected)
        self.worker.log_received.connect(self.append_log)
        self.worker.error_occurred.connect(self.append_error)
        self.worker.status_received.connect(self.append_status)
        self.worker.directory_updated.connect(self.on_directory_updated)
        self.worker.busy_changed.connect(self.on_busy_changed)
        self.worker.command_finished.connect(self.on_command_finished)

        self.thread.start()
        self._set_connected_ui(False)

    def _build_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.listWidget)
        layout.addWidget(self.logEdit)

        row = QHBoxLayout()
        row.addWidget(self.btnConnect)
        row.addWidget(self.btnDisconnect)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(self.btnCd)
        row.addWidget(self.btnDir)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(self.btnPlay)
        row.addWidget(self.btnStop)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(self.btnHelp)
        row.addWidget(self.btnSend)
        layout.addLayout(row)

        self.setLayout(layout)

    def _wire_ui(self) -> None:
        self.btnConnect.clicked.connect(self.click_connect)
        self.btnDisconnect.clicked.connect(self.click_disconnect)
        self.btnDir.clicked.connect(self.click_dir)
        self.btnCd.clicked.connect(self.click_cd)
        self.btnPlay.clicked.connect(self.click_play)
        self.btnStop.clicked.connect(self.click_stop)
        self.btnHelp.clicked.connect(self.click_help)
        self.btnSend.clicked.connect(self.click_send)
        self.listWidget.itemDoubleClicked.connect(self.double_click_list)

    def _emit(self, kind: CommandKind, **payload) -> None:
        self.request_command.emit(CommandRequest(kind=kind, payload=payload))

    def click_connect(self) -> None:
        self._emit(CommandKind.CONNECT, port_name=None, baudrate=19200, timeout=0.0)

    def click_disconnect(self) -> None:
        self._emit(CommandKind.DISCONNECT)

    def click_dir(self) -> None:
        self._emit(CommandKind.SD_DIR)

    def click_cd(self) -> None:
        item = self._current_dir_item()
        if item is None:
            return
        if not item.is_dir:
            self.append_log("> selected item is not a directory")
            return
        self._emit(CommandKind.CD, dirname=item.filename)

    def click_play(self) -> None:
        item = self._current_dir_item()
        if item is None:
            return
        if item.is_dir:
            self.append_log("> selected item is a directory")
            return
        self._emit(CommandKind.PLAY, filename=item.filename)

    def click_stop(self) -> None:
        self._emit(CommandKind.STOP)

    def click_help(self) -> None:
        self._emit(CommandKind.HELP)

    def click_send(self) -> None:
        text, ok = QInputDialog.getText(self, "Input command", "command:")
        if ok and text:
            self._emit(CommandKind.RAW, text=text)

    def double_click_list(self, _item) -> None:
        item = self._current_dir_item()
        if item is None:
            return
        if item.is_dir:
            self.click_cd()
        else:
            self.click_play()

    def _current_dir_item(self) -> DirItem | None:
        current = self.listWidget.currentItem()
        if current is None:
            return None
        return self._dirlist.find_item(current.text())

    @QtCore.Slot(str, int)
    def on_connected(self, port_name: str, baudrate: int) -> None:
        self.append_log(f"> connected: {port_name}, {baudrate} baud")
        self._set_connected_ui(True)
        self.click_dir()

    @QtCore.Slot()
    def on_disconnected(self) -> None:
        self.append_log("> disconnected")
        self._set_connected_ui(False)

    @QtCore.Slot(object)
    def on_directory_updated(self, dirlist: DirList) -> None:
        self._dirlist = dirlist
        self.listWidget.clear()
        self.listWidget.addItems([item.dispname for item in dirlist])
        self.append_log(f"> directory updated: {len(dirlist)} entries")

    @QtCore.Slot(bool)
    def on_busy_changed(self, busy: bool) -> None:
        for button in (self.btnDir, self.btnCd, self.btnPlay, self.btnStop, self.btnHelp, self.btnSend):
            button.setEnabled(not busy)

    @QtCore.Slot(object)
    def on_command_finished(self, result: CommandResult) -> None:
        state = "OK" if result.ok else "NG"
        self.append_log(f"> command finished: {result.kind.value} [{state}]")

    @QtCore.Slot(str)
    def append_log(self, text: str) -> None:
        if text:
            self.logEdit.append(text)

    @QtCore.Slot(str)
    def append_error(self, text: str) -> None:
        if text:
            self.logEdit.append(f"[ERROR] {text}")

    @QtCore.Slot(str)
    def append_status(self, text: str) -> None:
        if text:
            self.logEdit.append(f"[STATUS] {text}")

    def _set_connected_ui(self, connected: bool) -> None:
        self.btnConnect.setEnabled(not connected)
        self.btnDisconnect.setEnabled(connected)
        for button in (self.btnDir, self.btnCd, self.btnPlay, self.btnStop, self.btnHelp, self.btnSend):
            button.setEnabled(connected)

    def closeEvent(self, event) -> None:
        QtCore.QMetaObject.invokeMethod(self.worker, "request_stop", QtCore.Qt.BlockingQueuedConnection)
        self.thread.quit()
        self.thread.wait(3000)
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    form = Form()
    form.resize(700, 520)
    form.show()
    sys.exit(app.exec_())
