"""Background USB/device connection monitor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from config.settings import SETTINGS
from core.mode_detector import DeviceMode, UsbDeviceDescriptor, detect_current_mode


@dataclass
class ConnectionState:
    mode: DeviceMode = DeviceMode.DISCONNECTED
    descriptor: Optional[UsbDeviceDescriptor] = None
    is_paired: bool = False
    is_locked: bool = False
    status_message: str = "No device connected"
    error_code: Optional[str] = None
    info: dict | None = None


class DeviceMonitor(QObject):
    """Polls USB and lockdown state, emitting signals on change."""

    state_changed = pyqtSignal(object)  # ConnectionState
    device_connected = pyqtSignal(object)
    device_disconnected = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = ConnectionState()
        self._timer = QTimer(self)
        self._timer.setInterval(SETTINGS.poll_interval_ms)
        self._timer.timeout.connect(self._poll)

    def start(self) -> None:
        self._poll()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _poll(self) -> None:
        new_state = self._build_state()
        previous_mode = self._state.mode
        changed = (
            new_state.mode != self._state.mode
            or new_state.status_message != self._state.status_message
            or new_state.is_paired != self._state.is_paired
            or new_state.is_locked != self._state.is_locked
        )
        self._state = new_state

        if changed:
            self.state_changed.emit(self._state)
            if previous_mode == DeviceMode.DISCONNECTED and new_state.mode != DeviceMode.DISCONNECTED:
                self.device_connected.emit(self._state)
            elif previous_mode != DeviceMode.DISCONNECTED and new_state.mode == DeviceMode.DISCONNECTED:
                self.device_disconnected.emit()

    def _build_state(self) -> ConnectionState:
        mode, descriptor = detect_current_mode()

        if mode == DeviceMode.DISCONNECTED:
            return ConnectionState(
                mode=mode,
                status_message="No iPhone detected — connect your USB cable.",
            )

        if mode == DeviceMode.RECOVERY:
            return ConnectionState(
                mode=mode,
                descriptor=descriptor,
                is_paired=False,
                status_message="Recovery Mode — Full access without Trust!",
            )

        if mode == DeviceMode.DFU:
            return ConnectionState(
                mode=mode,
                descriptor=descriptor,
                is_paired=False,
                status_message="DFU Mode — Full access without Trust!",
            )

        # Normal mode — probe pairing/lock status
        return self._probe_normal_mode(descriptor)

    def _probe_normal_mode(self, descriptor: Optional[UsbDeviceDescriptor]) -> ConnectionState:
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.exceptions import (
                DeviceLockedError as PMDDeviceLockedError,
                NotPairedError,
                PasswordRequiredError,
            )

            lockdown = create_using_usbmux()
            info = lockdown.short_info
            name = info.get("DeviceName", "iPhone")
            return ConnectionState(
                mode=DeviceMode.NORMAL,
                descriptor=descriptor,
                is_paired=True,
                is_locked=False,
                status_message=f"Connected: {name}",
            )
        except Exception as exc:
            exc_name = type(exc).__name__
            if exc_name in ("NotPairedError",):
                return ConnectionState(
                    mode=DeviceMode.NORMAL,
                    descriptor=descriptor,
                    is_paired=False,
                    status_message="Trust not given — USB detected. Enter Recovery/DFU mode.",
                    error_code="PAIRING_REQUIRED",
                )
            if exc_name in ("DeviceLockedError", "PasswordRequiredError"):
                return ConnectionState(
                    mode=DeviceMode.NORMAL,
                    descriptor=descriptor,
                    is_paired=True,
                    is_locked=True,
                    status_message="Device locked — access via Recovery mode.",
                    error_code="DEVICE_LOCKED",
                )
            return ConnectionState(
                mode=DeviceMode.NORMAL,
                descriptor=descriptor,
                status_message=f"Connected with limited access: {exc}",
                error_code="PARTIAL_ACCESS",
            )

    @property
    def current_state(self) -> ConnectionState:
        return self._state
