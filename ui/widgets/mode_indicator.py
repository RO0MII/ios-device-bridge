"""Visual status badge with smooth color transitions."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

import config.settings as cfg
from core.mode_detector import DeviceMode
from utils.animation_utils import animate_color_transition

BADGE_COLORS_BW = {
    DeviceMode.DISCONNECTED: "#555555",
    DeviceMode.NORMAL: "#ffffff",
    DeviceMode.RECOVERY: "#aaaaaa",
    DeviceMode.DFU: "#888888",
    DeviceMode.UNKNOWN: "#666666",
}


class ModeIndicator(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setFixedHeight(44)
        self._current_mode = DeviceMode.DISCONNECTED

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(20)
        self._label = QLabel("Disconnected")
        self._label.setStyleSheet("font-weight: 600;")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch()

        self.set_mode(DeviceMode.DISCONNECTED)

    def set_mode(self, mode: DeviceMode) -> None:
        if mode == self._current_mode:
            return
        self._current_mode = mode

        color = BADGE_COLORS_BW.get(mode) if cfg.current_theme == "bw" else mode.badge_color
        self._dot.setStyleSheet(f"color: {color}; font-size: 16px;")
        self._label.setText(mode.label)
        self.setToolTip(f"Current device state: {mode.label}")

        anim = animate_color_transition(self._dot, 300)
        anim.start()
