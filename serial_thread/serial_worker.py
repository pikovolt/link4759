# coding: utf-8
from __future__ import annotations

import queue
import time
from typing import Optional

import serial
from serial.tools import list_ports
from PySide6 import QtCore

from .commands import CommandKind, CommandRequest, CommandResult
from .protocol import command_to_text, parse_dir_list, is_dir_command, classify_line


class SerialWorker(QtCore.QObject):
    """Serial communication worker.

    Design rule:
        This object is the only place that may touch serial.Serial.

    The worker lives in a QThread and is driven by a QTimer.
    This keeps the thread event loop alive and avoids QThread.terminate().
    """

    connected = QtCore.Signal(str, int)
    disconnected = QtCore.Signal()
    error_occurred = QtCore.Signal(str)
    log_received = QtCore.Signal(str)
    line_received = QtCore.Signal(str)
    status_received = QtCore.Signal(str)
    directory_updated = QtCore.Signal(object)
    busy_changed = QtCore.Signal(bool)
    command_finished = QtCore.Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial: Optional[serial.Serial] = None
        self._commands: "queue.Queue[CommandRequest]" = queue.Queue()
        self._recv_text_buffer = ""
        self._response_lines: list[str] = []
        self._active_command: Optional[CommandRequest] = None
        self._active_started_at = 0.0
        self._active_timeout_sec = 2.0
        self._running = False
        self._timer: Optional[QtCore.QTimer] = None

    @QtCore.Slot()
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self.log_received.emit("> serial worker started")

    @QtCore.Slot()
    def request_stop(self) -> None:
        self._running = False
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        self._clear_queue()
        self._close_serial()
        self.log_received.emit("> serial worker stopped")

    @QtCore.Slot(object)
    def enqueue(self, req: CommandRequest) -> None:
        self._commands.put(req)

    def _tick(self) -> None:
        if not self._running:
            return

        self._read_available()

        if self._active_command is not None:
            self._check_active_command()
            return

        try:
            req = self._commands.get_nowait()
        except queue.Empty:
            return

        self._begin_command(req)

    def _begin_command(self, req: CommandRequest) -> None:
        self._active_command = req
        self._active_started_at = time.monotonic()
        self._response_lines = []
        self.busy_changed.emit(True)

        try:
            if req.kind == CommandKind.CONNECT:
                self._handle_connect(req)
                self._finish_active(True, "connected")
                return

            if req.kind == CommandKind.DISCONNECT:
                self._close_serial()
                self._finish_active(True, "disconnected")
                return

            if self._serial is None or not self._serial.is_open:
                self._finish_active(False, "serial port is not open")
                return

            # Keep ownership local. Do not reset input buffer by default:
            # dropping incoming asynchronous text can hide real device state.
            text = command_to_text(req)
            self._serial.write((text + "\r").encode("utf-8"))
            self.log_received.emit(f">> {text}")

        except Exception as exc:
            self._finish_active(False, str(exc))

    def _check_active_command(self) -> None:
        req = self._active_command
        if req is None:
            return

        elapsed = time.monotonic() - self._active_started_at
        quiet_enough = elapsed > 0.25 and bool(self._response_lines)
        timed_out = elapsed > self._active_timeout_sec

        if quiet_enough or timed_out:
            response = "\n".join(self._response_lines)
            ok = not timed_out

            if is_dir_command(req):
                dirlist = parse_dir_list(response)
                self.directory_updated.emit(dirlist)
                self._finish_active(ok, response, data=dirlist)
            else:
                self._finish_active(ok, response)

    def _finish_active(self, ok: bool, message: str = "", data=None) -> None:
        req = self._active_command
        if req is None:
            return

        result = CommandResult(req.command_id, req.kind, ok, message, data)
        if not ok:
            self.error_occurred.emit(message)

        self.command_finished.emit(result)
        self._active_command = None
        self._response_lines = []
        self.busy_changed.emit(False)

    def _handle_connect(self, req: CommandRequest) -> None:
        payload = req.payload
        port_name = payload.get("port_name")
        baudrate = int(payload.get("baudrate", 19200))
        timeout = float(payload.get("timeout", 0.0))

        devices = [info.device for info in list_ports.comports()]
        if port_name is None:
            if not devices:
                raise RuntimeError("COM port not found")
            port_name = devices[0]
        elif port_name not in devices:
            raise RuntimeError(f"COM port not found: {port_name}; devices={devices}")

        self._close_serial()
        self._serial = serial.Serial(port=port_name, baudrate=baudrate, timeout=timeout, write_timeout=1.0)
        self.connected.emit(port_name, baudrate)

    def _close_serial(self) -> None:
        if self._serial is not None:
            try:
                if self._serial.is_open:
                    port_name = self._serial.port
                    self._serial.close()
                    self.log_received.emit(f"> {port_name} closed")
            finally:
                self._serial = None
                self.disconnected.emit()

    def _read_available(self) -> None:
        if self._serial is None or not self._serial.is_open:
            return
        try:
            waiting = self._serial.in_waiting
            if waiting <= 0:
                return
            data = self._serial.read(waiting)
            if not data:
                return
            text = data.decode("utf-8", errors="replace")
            self._recv_text_buffer += text
            self._drain_lines()
        except Exception as exc:
            self.error_occurred.emit(f"serial read failed: {exc}")

    def _drain_lines(self) -> None:
        while "\n" in self._recv_text_buffer:
            line, self._recv_text_buffer = self._recv_text_buffer.split("\n", 1)
            line = line.rstrip("\r")
            self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        self.line_received.emit(line)
        if self._active_command is not None:
            self._response_lines.append(line)

        kind = classify_line(line)
        if kind == "status":
            self.status_received.emit(line)
        elif kind == "error":
            self.error_occurred.emit(line)
        else:
            self.log_received.emit(line)

    def _clear_queue(self) -> None:
        try:
            while True:
                self._commands.get_nowait()
        except queue.Empty:
            pass
