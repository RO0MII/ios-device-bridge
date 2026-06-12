"""Locked Device panel — bypass passcode via Recovery/DFU, activation lock check."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

import config.settings as cfg
from core.device_monitor import ConnectionState
from core.device_manager import DeviceManager
from core.exceptions import DeviceBridgeError
from core.mode_detector import DeviceMode
from services.recovery_service import RecoveryService
from utils.animation_utils import animate_opacity, animate_spring_bounce


class LockStatusCard(QFrame):
    def __init__(self, title: str, value: str = "—", icon: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setMinimumHeight(80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("subtitle")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()

        self._value = QLabel(value)
        self._value.setStyleSheet("font-size: 20px; font-weight: 700; color: #ffffff;")

        layout.addLayout(header)
        layout.addWidget(self._value)

    def set_value(self, value: str) -> None:
        self._value.setText(value)
        animate_spring_bounce(self, 400).start()

    def set_color(self, color: str) -> None:
        self._value.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {color};")


class StepCard(QFrame):
    def __init__(self, number: str, title: str, body: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("stepCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        num = QLabel(number)
        num.setObjectName("stepNumber")
        num.setFixedSize(36, 36)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        t = QLabel(title)
        t.setStyleSheet("font-weight: 600; font-size: 14px; color: #ffffff;")
        b = QLabel(body)
        b.setObjectName("subtitle")
        b.setWordWrap(True)
        text_layout.addWidget(t)
        text_layout.addWidget(b)

        layout.addWidget(num)
        layout.addLayout(text_layout, 1)


class LockBreakPanel(QWidget):
    """Dedicated panel for handling locked / passcode-locked iPhones."""

    open_recovery_guide = pyqtSignal()
    open_dfu_wizard = pyqtSignal()

    def __init__(self, device_manager: DeviceManager | None = None, parent=None) -> None:
        super().__init__(parent)
        self._device_manager = device_manager or DeviceManager()
        self._recovery = RecoveryService()
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("heroBanner")
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(28, 24, 28, 24)
        t = QLabel("Locked Device — Bypass & Recovery")
        t.setObjectName("heroTitle")
        s = QLabel(
            "iPhone locked or passcode forgotten? Recovery and DFU modes "
            "give you full USB-level access without needing the passcode. "
            "Check lock status, bypass the lock screen, or restore firmware."
        )
        s.setObjectName("heroSubtitle")
        s.setWordWrap(True)
        hl.addWidget(t)
        hl.addWidget(s)
        layout.addWidget(hero)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self._card_lock = LockStatusCard("Device Lock", icon="")
        self._card_activation = LockStatusCard("Activation Lock", icon="")
        self._card_mode = LockStatusCard("Current Mode", icon="")
        self._card_recovery = LockStatusCard("Recovery Possible", icon="")
        status_row.addWidget(self._card_lock)
        status_row.addWidget(self._card_activation)
        status_row.addWidget(self._card_mode)
        status_row.addWidget(self._card_recovery)
        layout.addLayout(status_row)

        info_frame = QFrame()
        info_frame.setObjectName("glassPanel")
        il = QVBoxLayout(info_frame)
        il.setContentsMargins(24, 20, 24, 20)

        info_header = QHBoxLayout()
        info_title = QLabel("Lock State Details")
        info_title.setObjectName("sectionTitle")
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("accentButton")
        self._refresh_btn.clicked.connect(self.refresh)
        info_header.addWidget(info_title)
        info_header.addStretch()
        info_header.addWidget(self._refresh_btn)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Property", "Value"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        il.addLayout(info_header)
        il.addWidget(self._table)
        layout.addWidget(info_frame)

        unlock_frame = QFrame()
        unlock_frame.setObjectName("glassPanel")
        ul = QVBoxLayout(unlock_frame)
        ul.setContentsMargins(24, 20, 24, 20)

        ul_title = QLabel("Bypass Lock Screen — Step by Step")
        ul_title.setObjectName("sectionTitle")
        ul_sub = QLabel(
            "No passcode needed. Use Recovery Mode or DFU mode to access the "
            "device at the USB level. The screen lock only prevents touch input, "
            "not USB communication."
        )
        ul_sub.setObjectName("subtitle")
        ul_sub.setWordWrap(True)
        ul.addWidget(ul_title)
        ul.addSpacing(4)
        ul.addWidget(ul_sub)
        ul.addSpacing(12)

        steps_data = [
            (
                "1",
                "Force Restart (if needed)",
                "Press Volume Up, Volume Down, hold Side until Apple logo. "
                "If the device is unresponsive, this is the first step.",
            ),
            (
                "2",
                "Connect to PC",
                "Plug iPhone into computer via USB. The app will detect it "
                "even if the screen is locked.",
            ),
            (
                "3",
                "Enter Recovery Mode",
                "Press Volume Up, Volume Down, hold Side button until cable "
                "+ iTunes icon appears. Lock screen is bypassed in Recovery.",
            ),
            (
                "4",
                "Full USB Access",
                "Once in Recovery Mode, irecovery commands work without "
                "any passcode. ECID, device info, and restore all available.",
            ),
            (
                "5",
                "Restore or Exit",
                "In Recovery: click Exit Recovery to reboot, or select an "
                "IPSW to restore firmware (erases passcode).",
            ),
        ]
        for num, title, body in steps_data:
            ul.addWidget(StepCard(num, title, body))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self._recovery_btn = QPushButton("Recovery Guide")
        self._recovery_btn.clicked.connect(self.open_recovery_guide.emit)
        self._dfu_btn = QPushButton("DFU Wizard")
        self._dfu_btn.setObjectName("dangerButton")
        self._dfu_btn.clicked.connect(self.open_dfu_wizard.emit)
        self._force_restart_btn = QPushButton("Force Restart Guide")
        self._exit_recovery_btn = QPushButton("Exit Recovery")
        self._exit_recovery_btn.setObjectName("primaryButton")
        self._exit_recovery_btn.clicked.connect(self._handle_exit_recovery)

        btn_row.addWidget(self._recovery_btn)
        btn_row.addWidget(self._dfu_btn)
        btn_row.addWidget(self._force_restart_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._exit_recovery_btn)
        ul.addLayout(btn_row)
        layout.addWidget(unlock_frame)

        faq = QFrame()
        faq.setObjectName("glassPanel")
        fl = QVBoxLayout(faq)
        fl.setContentsMargins(24, 20, 24, 20)

        faq_title = QLabel("Lock Bypass — FAQ")
        faq_title.setObjectName("sectionTitle")
        fl.addWidget(faq_title)
        fl.addSpacing(8)

        faqs = [
            ("Can I remove the passcode without restoring?",
             "No. The passcode is stored in the Secure Enclave and cannot be read "
             "or modified via USB. Restoring via Recovery/DFU is the only way to clear it."),
            ("Can I backup data from a locked iPhone?",
             "If the iPhone is locked and NOT paired (no 'Trust This Computer'), "
             "you cannot backup via iTunes. Recovery/DFU mode allows restore only."),
            ("What is Activation Lock / iCloud Lock?",
             "Activation Lock ties the iPhone to the owner's Apple ID. Recovery/DFU "
             "restore will clear the passcode but NOT the iCloud lock. Original owner "
             "credentials are required to fully activate the device after restore."),
            ("Does Recovery Mode work with a broken screen?",
             "Yes. Recovery Mode uses hardware buttons only (Volume + Side). "
             "No screen interaction needed."),
        ]
        for q, a in faqs:
            q_lbl = QLabel(q)
            q_lbl.setStyleSheet("font-weight: 600; color: #ffffff; padding-top: 10px;")
            a_lbl = QLabel(a)
            a_lbl.setObjectName("subtitle")
            a_lbl.setWordWrap(True)
            fl.addWidget(q_lbl)
            fl.addWidget(a_lbl)

        layout.addWidget(faq)

        layout.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        try:
            snapshot = self._device_manager.get_snapshot()
            mode = snapshot.mode

            is_locked = snapshot.error_code == "DEVICE_LOCKED"
            is_recovery = mode in (DeviceMode.RECOVERY, DeviceMode.DFU)

            if is_locked:
                self._card_lock.set_value("Locked")
                self._card_lock.set_color("#f85149")
            elif is_recovery:
                self._card_lock.set_value("Bypassed (Recovery)")
                self._card_lock.set_color("#3fb950")
            elif mode == DeviceMode.NORMAL:
                self._card_lock.set_value("Unlocked")
                self._card_lock.set_color("#3fb950")
            else:
                self._card_lock.set_value("—")
                self._card_lock.set_color("#ffffff")

            activation = snapshot.info.get("Activation State", "Unknown")
            self._card_activation.set_value(activation)

            self._card_mode.set_value(mode.label)
            self._card_recovery.set_value("Yes" if is_recovery or mode == DeviceMode.NORMAL else "No")

            self._table.setRowCount(0)
            rows = [("Mode", mode.label)]

            if snapshot.error_code:
                rows.append(("Error Code", snapshot.error_code))
            if snapshot.connection_message:
                rows.append(("Message", snapshot.connection_message))

            rows.extend([
                ("Passcode Status", "Locked" if is_locked else "Unlocked / Not needed"),
                ("USB Access", "Full (Recovery)" if is_recovery else "Limited (Normal)"),
                ("Restore Possible", "Yes" if is_recovery else "No — enter Recovery first"),
            ])

            if snapshot.info:
                for k, v in snapshot.info.items():
                    if k not in ("Model", "iOS Version", "UDID", "Serial Number", "Activation State"):
                        rows.append((k, str(v)))

            self._table.setRowCount(len(rows))
            for r, (k, v) in enumerate(rows):
                self._table.setItem(r, 0, QTableWidgetItem(k))
                self._table.setItem(r, 1, QTableWidgetItem(v))

            self._exit_recovery_btn.setEnabled(is_recovery)

        except DeviceBridgeError as exc:
            self._card_lock.set_value("Not connected")
            self._card_activation.set_value("—")
            self._card_mode.set_value("Disconnected")
            self._card_recovery.set_value("No")
            self._exit_recovery_btn.setEnabled(False)

            self._table.setRowCount(1)
            self._table.setItem(0, 0, QTableWidgetItem("Status"))
            self._table.setItem(0, 1, QTableWidgetItem(str(exc)))

    def update_from_state(self, state: ConnectionState) -> None:
        self.refresh()

    def _handle_exit_recovery(self) -> None:
        try:
            self._device_manager.exit_recovery_mode()
            QMessageBox.information(self, "Recovery", "Exit Recovery command sent. Device will reboot.")
        except DeviceBridgeError as exc:
            QMessageBox.warning(self, "Recovery Error", str(exc))
