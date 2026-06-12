"""Connection status banner with smooth state transitions and breathing pulse."""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsOpacityEffect

import config.settings as cfg
from core.device_monitor import ConnectionState
from core.mode_detector import DeviceMode
from utils.animation_utils import animate_breathing, ease_out_curve


class ConnectionStatusBanner(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        self._title = QLabel("Connection Status")
        self._title.setObjectName("sectionTitle")

        self._message = QLabel("Waiting for device...")
        self._message.setWordWrap(True)
        self._message.setStyleSheet("font-size: 15px; font-weight: 600;")

        self._detail = QLabel("")
        self._detail.setObjectName("subtitle")
        self._detail.setWordWrap(True)

        layout.addWidget(self._title)
        layout.addWidget(self._message)
        layout.addWidget(self._detail)

        self._message_effect = QGraphicsOpacityEffect(self._message)
        self._message.setGraphicsEffect(self._message_effect)

        self._breathing_anim = None

    def update_state(self, state: ConnectionState) -> None:
        self._message.setText(state.status_message)

        fade = QPropertyAnimation(self._message_effect, b"opacity")
        fade.setDuration(350)
        fade.setKeyValueAt(0, 0.2)
        fade.setKeyValueAt(0.4, 1.2)
        fade.setEndValue(1.0)
        fade.setEasingCurve(ease_out_curve())
        fade.start()

        details = []
        if state.mode != DeviceMode.DISCONNECTED:
            details.append(f"Mode: {state.mode.label}")
        if state.is_paired:
            details.append("Paired: Yes")
        elif state.mode == DeviceMode.NORMAL:
            details.append("Paired: No — trust required")
        if state.is_locked:
            details.append("Lock: Device locked")
        if state.error_code:
            details.append(f"Code: {state.error_code}")

        self._detail.setText(" · ".join(details))

        if cfg.current_theme == "bw":
            if state.mode == DeviceMode.DISCONNECTED:
                self._message.setStyleSheet("color: #666666; font-weight: 600; font-size: 15px;")
            else:
                self._message.setStyleSheet("color: #ffffff; font-weight: 600; font-size: 15px;")
        elif state.mode in (DeviceMode.RECOVERY, DeviceMode.DFU):
            self._message.setStyleSheet("color: #3fb950; font-weight: 600; font-size: 15px;")
        elif state.error_code in ("PAIRING_REQUIRED", "DEVICE_LOCKED"):
            self._message.setStyleSheet("color: #d29922; font-weight: 600; font-size: 15px;")
        elif state.mode == DeviceMode.DISCONNECTED:
            self._message.setStyleSheet("color: #8b949e; font-weight: 600; font-size: 15px;")
        else:
            self._message.setStyleSheet("color: #3fb950; font-weight: 600; font-size: 15px;")

        if self._breathing_anim:
            self._breathing_anim.stop()
        if state.mode not in (DeviceMode.DISCONNECTED,):
            self._breathing_anim = animate_breathing(self._message, 2500)
            self._breathing_anim.start()
