"""Main dashboard with iOS-style glass cards, spring animations, and extended stats."""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGraphicsOpacityEffect,
)

from core.device_monitor import ConnectionState
from core.mode_detector import DeviceMode
from ui.widgets.connection_status import ConnectionStatusBanner
from ui.widgets.mode_indicator import ModeIndicator
from utils.animation_utils import spring_curve, animate_spring_bounce, animate_staggered_reveal


class GlassCard(QFrame):
    def __init__(self, title: str, value: str = "—", icon: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setMinimumHeight(90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        self._icon = QLabel(icon)
        self._icon.setStyleSheet("font-size: 18px;")
        self._icon.setVisible(bool(icon))
        self._title = QLabel(title)
        self._title.setObjectName("subtitle")
        header.addWidget(self._icon)
        header.addWidget(self._title)
        header.addStretch()

        self._value = QLabel(value)
        self._value.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        self._value.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(self._value)

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)

    def set_value(self, value: str) -> None:
        self._value.setText(value)
        bounce = animate_spring_bounce(self, 400)
        bounce.start()

    def set_icon(self, icon: str) -> None:
        self._icon.setText(icon)
        self._icon.setVisible(bool(icon))

    def fade_in(self, delay_ms: int = 0) -> None:
        anim = QPropertyAnimation(self._opacity, b"opacity")
        anim.setDuration(500)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(spring_curve())
        if delay_ms:
            anim.setLoopCount(1)
        anim.start()

class DashboardPanel(QFrame):

    exit_recovery_requested = pyqtSignal()
    enter_recovery_requested = pyqtSignal()
    force_recovery_requested = pyqtSignal()
    dfu_wizard_requested = pyqtSignal()
    restore_requested = pyqtSignal()
    reboot_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("heroBanner")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 22, 28, 22)
        hero_title = QLabel("iOS Device Dashboard")
        hero_title.setObjectName("heroTitle")
        hero_sub = QLabel(
            "Monitor and manage your connected iPhone in real-time. "
            "View device status, battery health, storage info, and more."
        )
        hero_sub.setObjectName("heroSubtitle")
        hero_sub.setWordWrap(True)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_sub)
        layout.addWidget(hero)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        self._mode_indicator = ModeIndicator()
        self._connection_banner = ConnectionStatusBanner()
        top_row.addWidget(self._mode_indicator, 1)
        top_row.addWidget(self._connection_banner, 3)
        layout.addLayout(top_row)

        cards = QGridLayout()
        cards.setSpacing(12)
        self._card_mode = GlassCard("Device Mode", icon="")
        self._card_status = GlassCard("Connection", icon="")
        self._card_pairing = GlassCard("Trust Status", icon="")
        self._card_usb = GlassCard("USB Product ID", icon="")
        self._card_ios = GlassCard("iOS Version", icon="")
        self._card_battery = GlassCard("Battery Health", icon="")
        self._card_storage = GlassCard("Storage", icon="")
        self._card_model = GlassCard("Model", icon="")
        cards.addWidget(self._card_mode, 0, 0)
        cards.addWidget(self._card_status, 0, 1)
        cards.addWidget(self._card_pairing, 0, 2)
        cards.addWidget(self._card_usb, 0, 3)
        cards.addWidget(self._card_ios, 1, 0)
        cards.addWidget(self._card_battery, 1, 1)
        cards.addWidget(self._card_storage, 1, 2)
        cards.addWidget(self._card_model, 1, 3)
        layout.addLayout(cards)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self._exit_recovery_btn = QPushButton("Exit Recovery")
        self._exit_recovery_btn.setObjectName("primaryButton")
        self._exit_recovery_btn.clicked.connect(self.exit_recovery_requested.emit)

        self._enter_recovery_btn = QPushButton("Enter Recovery")
        self._enter_recovery_btn.setToolTip(
            "Trigger recovery mode from a paired device in normal mode"
        )
        self._enter_recovery_btn.clicked.connect(self.enter_recovery_requested.emit)

        self._reboot_btn = QPushButton("Reboot Device")
        self._reboot_btn.setObjectName("accentButton")
        self._reboot_btn.setToolTip("Reboot device in recovery/DFU mode")
        self._reboot_btn.clicked.connect(self.reboot_requested.emit)

        self._dfu_wizard_btn = QPushButton("DFU Wizard")
        self._dfu_wizard_btn.setObjectName("dangerButton")
        self._dfu_wizard_btn.setToolTip("Guided DFU entry with timer")
        self._dfu_wizard_btn.clicked.connect(self.dfu_wizard_requested.emit)

        self._force_recovery_btn = QPushButton("Force Recovery")
        self._force_recovery_btn.setToolTip("Force device into recovery mode via USB")
        self._force_recovery_btn.clicked.connect(self.force_recovery_requested.emit)

        self._restore_btn = QPushButton("Restore iPhone")
        self._restore_btn.setObjectName("restoreButton")
        self._restore_btn.setToolTip("Restore device using IPSW firmware")
        self._restore_btn.clicked.connect(self.restore_requested.emit)

        actions.addWidget(self._exit_recovery_btn)
        actions.addWidget(self._enter_recovery_btn)
        actions.addWidget(self._force_recovery_btn)
        actions.addWidget(self._reboot_btn)
        actions.addWidget(self._dfu_wizard_btn)
        actions.addWidget(self._restore_btn)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()

        self._update_action_buttons(DeviceMode.DISCONNECTED)

        self._cards = [
            self._card_mode, self._card_status, self._card_pairing,
            self._card_usb, self._card_ios, self._card_battery,
            self._card_storage, self._card_model,
        ]

    def animate_cards(self) -> None:
        anim = animate_staggered_reveal(self._cards, 500)
        anim.start()

    def update_state(self, state: ConnectionState) -> None:
        self._mode_indicator.set_mode(state.mode)
        self._connection_banner.update_state(state)

        self._card_mode.set_value(state.mode.label)
        self._card_status.set_value(
            "Locked" if state.is_locked
            else ("Connected" if state.mode != DeviceMode.DISCONNECTED else "None")
        )
        self._card_pairing.set_value(
            "Trusted" if state.is_paired
            else ("Not Trusted" if state.mode == DeviceMode.NORMAL else "Not Required")
        )
        product_id = (
            f"0x{state.descriptor.product_id:04X}"
            if state.descriptor
            else "—"
        )
        self._card_usb.set_value(product_id)

        if state.info:
            self._card_ios.set_value(state.info.get("iOS Version", "—"))
            self._card_model.set_value(state.info.get("Model", "—"))
            battery = state.info.get("Battery Health", "—")
            self._card_battery.set_value(f"{battery}%" if isinstance(battery, (int, float)) else str(battery))
            storage = state.info.get("Storage", "—")
            self._card_storage.set_value(str(storage) if storage != "—" else "—")
        else:
            self._card_ios.set_value("—")
            self._card_model.set_value("—")
            self._card_battery.set_value("—")
            self._card_storage.set_value("—")

        self._update_action_buttons(state.mode)

    def update_info(self, info: dict) -> None:
        if info:
            self._card_ios.set_value(info.get("iOS Version", self._card_ios._value.text()))
            self._card_model.set_value(info.get("Model", self._card_model._value.text()))
            battery = info.get("Battery Health")
            if battery:
                self._card_battery.set_value(f"{battery}%" if isinstance(battery, (int, float)) else str(battery))
            storage = info.get("Storage")
            if storage:
                self._card_storage.set_value(str(storage))

    def _update_action_buttons(self, mode: DeviceMode) -> None:
        is_recovery = mode == DeviceMode.RECOVERY
        is_normal = mode == DeviceMode.NORMAL
        is_connected = mode != DeviceMode.DISCONNECTED
        self._exit_recovery_btn.setEnabled(is_recovery)
        self._enter_recovery_btn.setEnabled(is_normal)
        self._force_recovery_btn.setEnabled(is_connected and not is_recovery)
        self._reboot_btn.setEnabled(is_recovery or mode == DeviceMode.DFU)
        self._restore_btn.setEnabled(is_recovery or mode == DeviceMode.DFU)
        self._dfu_wizard_btn.setEnabled(is_connected)
