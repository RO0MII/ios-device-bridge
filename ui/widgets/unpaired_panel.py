"""Access device without Trust — Recovery/DFU mode panel with restore support."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
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
from core.device_manager import DeviceManager
from core.exceptions import DeviceBridgeError, RecoveryCommandError
from core.mode_detector import DeviceMode
from services.unpaired_service import UnpairedAccessService


class AccessLevelBadge(QFrame):
    COLORS = {
        "none": ("#6e7681", "Not connected"),
        "usb_only": ("#d29922", "USB only — Trust required"),
        "full_recovery": ("#3fb950", "Full access — Recovery Mode"),
        "full_dfu": ("#f85149", "Full access — DFU Mode"),
        "limited": ("#8b949e", "Limited access"),
    }

    COLORS_BW = {
        "none": ("#555555", "Not connected"),
        "usb_only": ("#888888", "USB only — Trust required"),
        "full_recovery": ("#aaaaaa", "Full access — Recovery Mode"),
        "full_dfu": ("#666666", "Full access — DFU Mode"),
        "limited": ("#777777", "Limited access"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        self._icon = QLabel("")
        self._icon.setStyleSheet("font-size: 20px;")
        self._label = QLabel("Not connected")
        self._label.setStyleSheet("font-size: 15px; font-weight: 600;")
        layout.addWidget(self._icon)
        layout.addWidget(self._label)
        layout.addStretch()
        self.set_level("none")

    def set_level(self, level: str) -> None:
        palette = self.COLORS_BW if cfg.current_theme == "bw" else self.COLORS
        color, text = palette.get(level, palette["limited"])
        self._label.setText(text)
        self.setStyleSheet(
            "QFrame#glassPanel {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08), "
            f"    stop:1 rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.03));"
            f"  border: 1px solid {color}44;"
            f"  border-radius: 12px;"
            "}"
        )


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
        text_layout.setSpacing(4)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: 600; font-size: 14px; color: #ffffff;")
        body_lbl = QLabel(body)
        body_lbl.setObjectName("subtitle")
        body_lbl.setWordWrap(True)
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(body_lbl)

        layout.addWidget(num)
        layout.addLayout(text_layout, 1)


class UnpairedAccessPanel(QWidget):
    open_dfu_wizard = pyqtSignal()
    open_recovery_guide = pyqtSignal()

    def __init__(self, device_manager: DeviceManager | None = None, parent=None) -> None:
        super().__init__(parent)
        self._service = UnpairedAccessService()
        self._device_manager = device_manager or DeviceManager()
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        hero = QFrame()
        hero.setObjectName("heroBanner")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_title = QLabel("Access iPhone Without Trust")
        hero_title.setObjectName("heroTitle")
        hero_sub = QLabel(
            "Even if the screen is broken or you can't tap 'Trust This Computer', "
            "you can still access your device in Recovery or DFU mode. "
            "Full USB-level access, no pairing required."
        )
        hero_sub.setObjectName("heroSubtitle")
        hero_sub.setWordWrap(True)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_sub)
        layout.addWidget(hero)

        self._access_badge = AccessLevelBadge()
        layout.addWidget(self._access_badge)

        info_frame = QFrame()
        info_frame.setObjectName("glassPanel")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(24, 20, 24, 20)

        info_header = QHBoxLayout()
        info_title = QLabel("USB Device Details (No Trust Needed)")
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

        info_layout.addLayout(info_header)
        info_layout.addWidget(self._table)
        layout.addWidget(info_frame)

        restore_frame = QFrame()
        restore_frame.setObjectName("glassPanel")
        restore_layout = QVBoxLayout(restore_frame)
        restore_layout.setContentsMargins(24, 20, 24, 20)

        restore_title = QLabel("Restore iPhone")
        restore_title.setObjectName("sectionTitle")
        restore_sub = QLabel(
            "Restore firmware on a device in Recovery or DFU mode. "
            "You will need an IPSW firmware file compatible with your iPhone model."
        )
        restore_sub.setObjectName("subtitle")
        restore_sub.setWordWrap(True)

        restore_btn_row = QHBoxLayout()
        self._restore_btn = QPushButton("Select IPSW & Restore")
        self._restore_btn.setObjectName("restoreButton")
        self._restore_btn.clicked.connect(self._handle_restore)
        self._restore_btn.setEnabled(False)
        restore_btn_row.addWidget(self._restore_btn)
        restore_btn_row.addStretch()

        restore_layout.addWidget(restore_title)
        restore_layout.addSpacing(4)
        restore_layout.addWidget(restore_sub)
        restore_layout.addSpacing(12)
        restore_layout.addLayout(restore_btn_row)
        layout.addWidget(restore_frame)

        steps_frame = QFrame()
        steps_frame.setObjectName("glassPanel")
        steps_layout = QVBoxLayout(steps_frame)
        steps_layout.setContentsMargins(24, 20, 24, 20)
        steps_title = QLabel("How to Access Without Screen / Trust")
        steps_title.setObjectName("sectionTitle")
        steps_layout.addWidget(steps_title)

        steps = [
            ("1", "Connect USB", "Plug your iPhone into the computer using a USB cable."),
            ("2", "Enter Recovery Mode", "Use the Side + Volume Down button method to enter Recovery Mode."),
            ("3", "App Detects Device", "The table above will show Mode = Recovery Mode automatically."),
            ("4", "Full Access", "ECID, Product, Mode — all read without Trust."),
            ("5", "Restore (Optional)", "Select an IPSW file and restore firmware in Recovery/DFU mode."),
        ]
        for num, title, body in steps:
            steps_layout.addWidget(StepCard(num, title, body))

        btn_row = QHBoxLayout()
        self._recovery_btn = QPushButton("Recovery Guide")
        self._recovery_btn.clicked.connect(self.open_recovery_guide.emit)
        self._dfu_btn = QPushButton("DFU Wizard")
        self._dfu_btn.setObjectName("dangerButton")
        self._dfu_btn.clicked.connect(self.open_dfu_wizard.emit)
        btn_row.addWidget(self._recovery_btn)
        btn_row.addWidget(self._dfu_btn)
        btn_row.addStretch()
        steps_layout.addLayout(btn_row)
        layout.addWidget(steps_frame)

        compare = QFrame()
        compare.setObjectName("glassPanel")
        compare_layout = QVBoxLayout(compare)
        compare_layout.setContentsMargins(24, 20, 24, 20)
        compare_title = QLabel("Access Level by Mode")
        compare_title.setObjectName("sectionTitle")
        compare_layout.addWidget(compare_title)

        compare_table = QTableWidget(4, 3)
        compare_table.setHorizontalHeaderLabels(["Mode", "Trust Needed?", "Access Level"])
        compare_table.verticalHeader().setVisible(False)
        compare_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        rows = [
            ("Normal", "Yes", "USB detection only"),
            ("Recovery", "No", "Full — irecovery commands"),
            ("DFU", "No", "Full — firmware restore"),
            ("Locked Screen", "—", "Use Recovery/DFU mode"),
        ]
        compare_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                compare_table.setItem(r, c, QTableWidgetItem(val))
        compare_table.horizontalHeader().setStretchLastSection(True)
        compare_layout.addWidget(compare_table)
        layout.addWidget(compare)

        layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        info = self._service.fetch_usb_info()
        level = info.get("access_level", "none")
        self._access_badge.set_level(level)

        rows: list[tuple[str, str]] = []
        if info.get("status") == "disconnected":
            rows.append(("Status", "iPhone not detected — connect via USB"))
        else:
            for key, value in info.items():
                if key in ("status", "access_level", "trust_required"):
                    continue
                rows.append((key, str(value)))

        self._table.setRowCount(len(rows))
        for r, (key, val) in enumerate(rows):
            self._table.setItem(r, 0, QTableWidgetItem(key))
            self._table.setItem(r, 1, QTableWidgetItem(val))

        mode = info.get("mode", "")
        self._restore_btn.setEnabled("Recovery" in mode or "DFU" in mode)

    def update_from_state(self, mode: DeviceMode) -> None:
        self.refresh()

    def _handle_restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select IPSW Firmware File",
            "",
            "IPSW Files (*.ipsw);;All Files (*.*)",
        )
        if not path:
            return

        reply = QMessageBox.warning(
            self,
            "Restore iPhone",
            "This will ERASE all data on your iPhone and install the "
            f"selected firmware:\n\n{path}\n\n"
            "Device must be in Recovery or DFU mode.\n"
            "This cannot be undone.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            proc = self._device_manager.restore_device(path)
            QMessageBox.information(
                self,
                "Restore Started",
                "Restore process has started.\n"
                "DO NOT disconnect the device during restore.",
            )
        except DeviceBridgeError as exc:
            QMessageBox.warning(self, "Restore Error", str(exc))
