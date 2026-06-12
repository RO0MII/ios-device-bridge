"""Primary application window with animated sidebar navigation."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup

from utils.animation_utils import spring_curve, ease_out_curve, animate_opacity
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

import config.settings as cfg
from config.settings import PROJECT_ROOT, SETTINGS
from core.device_manager import DeviceManager
from core.device_monitor import ConnectionState, DeviceMonitor
from core.exceptions import DeviceBridgeError
from ui.widgets.backup_panel import BackupPanel
from ui.widgets.dashboard import DashboardPanel
from ui.widgets.device_info_panel import DeviceInfoPanel
from ui.widgets.event_log import EventLogPanel
from ui.widgets.guides.dfu_guide import DfuGuidePanel
from ui.widgets.guides.dfu_wizard import DfuWizardDialog
from ui.widgets.guides.recovery_guide import RecoveryGuidePanel
from ui.widgets.ipsw_manager import IPSWManagerPanel
from ui.widgets.lock_break_panel import LockBreakPanel
from ui.widgets.restore_monitor import RestoreMonitorPanel
from ui.widgets.unpaired_panel import UnpairedAccessPanel


THEME_LABELS = {
    "glass": "Glass",
    "dark": "Dark",
    "bw": "B&W",
}

THEME_CYCLE = ["glass", "dark", "bw"]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._device_manager = DeviceManager()
        self._monitor = DeviceMonitor(self)

        self.setWindowTitle(f"{SETTINGS.app_name} v{SETTINGS.app_version}")
        self.setMinimumSize(SETTINGS.window_min_width, SETTINGS.window_min_height)
        self._apply_theme()
        self._build_ui()
        self._wire_signals()
        self._monitor.start()

    def _toggle_theme(self) -> None:
        idx = THEME_CYCLE.index(cfg.current_theme)
        next_theme = THEME_CYCLE[(idx + 1) % len(THEME_CYCLE)]
        self._apply_theme(next_theme)
        self._theme_btn.setText(f"Theme: {THEME_LABELS[next_theme]}")

    def _apply_theme(self, theme: str | None = None) -> None:
        theme = theme or cfg.current_theme
        qss_path = PROJECT_ROOT / "ui" / "themes" / f"{theme}_theme.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        cfg.current_theme = theme

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = self._build_sidebar()

        content_wrapper = QFrame()
        content_wrapper.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()

        self._dashboard = self._wrap_page(DashboardPanel())
        self._unpaired = self._wrap_page(UnpairedAccessPanel(self._device_manager))
        self._device_info = self._wrap_page(DeviceInfoPanel(self._device_manager))
        self._lock_break = self._wrap_page(LockBreakPanel(self._device_manager))
        self._recovery_guide = self._wrap_page(RecoveryGuidePanel())
        self._dfu_guide = self._wrap_page(DfuGuidePanel())
        self._backup = self._wrap_page(BackupPanel())
        self._event_log = self._wrap_page(EventLogPanel())
        self._ipsw_manager = self._wrap_page(IPSWManagerPanel())
        self._restore_monitor = self._wrap_page(RestoreMonitorPanel())

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._unpaired)
        self._stack.addWidget(self._device_info)
        self._stack.addWidget(self._lock_break)
        self._stack.addWidget(self._restore_monitor)
        self._stack.addWidget(self._ipsw_manager)
        self._stack.addWidget(self._event_log)
        self._stack.addWidget(self._backup)
        self._stack.addWidget(self._recovery_guide)
        self._stack.addWidget(self._dfu_guide)

        content_layout.addWidget(self._stack)
        root.addWidget(sidebar)
        root.addWidget(content_wrapper, 1)

        status = QStatusBar()
        status.showMessage("Ready — Connect your iPhone via USB")
        self.setStatusBar(status)
        self._status_bar = status

    def _wrap_page(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(widget)
        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 28, 12, 28)
        layout.setSpacing(2)

        logo = QLabel("◉")
        logo.setObjectName("appLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel(SETTINGS.app_name)
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("iOS Device Manager")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        self._nav_buttons: list[QPushButton] = []
        nav_items = [
            ("Dashboard", 0),
            ("Without Trust", 1),
            ("Device Info", 2),
            ("Lock Break", 3),
            ("Restore Monitor", 4),
            ("IPSW Manager", 5),
            ("Event Log", 6),
            ("Backup & Restore", 7),
            ("Recovery Guide", 8),
            ("DFU Guide", 9),
        ]
        for label, index in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setProperty("active", index == 0)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._navigate(i))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        sep = QFrame()
        sep.setObjectName("sidebarDivider")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        self._theme_btn = QPushButton(f"Theme: {THEME_LABELS[cfg.current_theme]}")
        self._theme_btn.setObjectName("themeButton")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._theme_btn.setToolTip("Cycle through themes: Glass → Dark → B&W")
        layout.addWidget(self._theme_btn)

        version = QLabel(f"v{SETTINGS.app_version}")
        version.setObjectName("subtitle")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        return sidebar

    def _navigate(self, index: int) -> None:
        current = self._stack.currentIndex()
        direction = 1 if index > current else -1

        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        old_widget = self._stack.currentWidget()
        self._stack.setCurrentIndex(index)
        new_widget = self._stack.currentWidget()

        if old_widget and new_widget and old_widget != new_widget:
            start_x = 60 * direction
            old_pos = old_widget.pos()
            new_widget.move(old_pos.x() + start_x, old_pos.y())

            group = QParallelAnimationGroup()

            slide_in = QPropertyAnimation(new_widget, b"pos")
            slide_in.setDuration(400)
            slide_in.setStartValue(QPoint(old_pos.x() + start_x, old_pos.y()))
            slide_in.setEndValue(old_pos)
            slide_in.setEasingCurve(spring_curve())
            group.addAnimation(slide_in)

            fade_in = animate_opacity(new_widget, 350, 0.0, 1.0)
            group.addAnimation(fade_in)

            slide_out = QPropertyAnimation(old_widget, b"pos")
            slide_out.setDuration(300)
            slide_out.setStartValue(old_pos)
            slide_out.setEndValue(QPoint(old_pos.x() - start_x, old_pos.y()))
            slide_out.setEasingCurve(ease_out_curve())
            group.addAnimation(slide_out)

            group.start()

        if index == 1:
            self._unpaired_panel().refresh()
        elif index == 2:
            self._device_info_panel().refresh()
        elif index == 3:
            self._lock_break_panel().refresh()

    def _panel_from_stack(self, index: int):
        scroll = self._stack.widget(index)
        return scroll.widget().layout().itemAt(0).widget()

    def _unpaired_panel(self) -> UnpairedAccessPanel:
        return self._panel_from_stack(1)

    def _device_info_panel(self) -> DeviceInfoPanel:
        return self._panel_from_stack(2)

    def _lock_break_panel(self) -> LockBreakPanel:
        return self._panel_from_stack(3)

    def _dashboard_panel(self) -> DashboardPanel:
        return self._panel_from_stack(0)

    def _wire_signals(self) -> None:
        dash = self._dashboard_panel()
        unpaired = self._unpaired_panel()
        lock_break = self._lock_break_panel()

        self._monitor.state_changed.connect(self._on_state_changed)
        self._monitor.device_connected.connect(self._on_device_connected)
        self._monitor.device_disconnected.connect(self._on_device_disconnected)
        dash.exit_recovery_requested.connect(self._handle_exit_recovery)
        dash.enter_recovery_requested.connect(self._handle_enter_recovery)
        dash.force_recovery_requested.connect(self._handle_enter_recovery)
        dash.reboot_requested.connect(self._handle_reboot_device)
        dash.dfu_wizard_requested.connect(self._open_dfu_wizard)
        dash.restore_requested.connect(self._handle_restore)
        unpaired.open_dfu_wizard.connect(self._open_dfu_wizard)
        unpaired.open_recovery_guide.connect(lambda: self._navigate(4))
        lock_break.open_recovery_guide.connect(lambda: self._navigate(4))
        lock_break.open_dfu_wizard.connect(self._open_dfu_wizard)

        self._info_timer = QTimer(self)
        self._info_timer.setInterval(SETTINGS.device_info_refresh_ms)
        self._info_timer.timeout.connect(self._maybe_refresh)
        self._info_timer.start()

    def _on_state_changed(self, state: ConnectionState) -> None:
        self._dashboard_panel().update_state(state)
        self._unpaired_panel().update_from_state(state.mode)
        self._lock_break_panel().update_from_state(state)
        self._status_bar.showMessage(state.status_message)

        if state.error_code == "PAIRING_REQUIRED":
            if self._stack.currentIndex() == 0:
                self._navigate(1)
        elif state.error_code == "DEVICE_LOCKED":
            if self._stack.currentIndex() == 0:
                self._navigate(3)

    def _on_device_connected(self, state: ConnectionState) -> None:
        self._status_bar.showMessage(f"Device detected — {state.mode.label}")

    def _on_device_disconnected(self) -> None:
        self._status_bar.showMessage("Device disconnected")
        self._device_info_panel().refresh()
        self._unpaired_panel().refresh()
        self._lock_break_panel().refresh()

    def _maybe_refresh(self) -> None:
        idx = self._stack.currentIndex()
        try:
            snapshot = self._device_manager.get_snapshot()
            if idx == 0:
                dash = self._dashboard_panel()
                if snapshot.info:
                    dash.update_info(snapshot.info)
        except Exception:
            pass

    def _handle_exit_recovery(self) -> None:
        try:
            self._device_manager.exit_recovery_mode()
            QMessageBox.information(self, "Recovery", "Exit Recovery command sent.")
        except DeviceBridgeError as exc:
            QMessageBox.warning(self, "Recovery Error", str(exc))

    def _handle_reboot_device(self) -> None:
        try:
            self._device_manager.reboot_device()
            QMessageBox.information(self, "Reboot", "Reboot command sent.")
        except DeviceBridgeError as exc:
            QMessageBox.warning(self, "Reboot Error", str(exc))

    def _handle_enter_recovery(self) -> None:
        reply = QMessageBox.question(
            self,
            "Enter Recovery Mode",
            "This will reboot your device into Recovery Mode.\n"
            "(Requires Trust + Unlock — if screen is broken, use hardware buttons)\n\n"
            "Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._device_manager.reboot_to_recovery()
                QMessageBox.information(self, "Recovery", "Recovery reboot command sent.")
            except DeviceBridgeError as exc:
                QMessageBox.warning(self, "Recovery Error", str(exc))

    def _handle_restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select IPSW Firmware File",
            cfg.IPSW_DOWNLOAD_DIR,
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
                "Restore process has started in the background.\n"
                "Monitor the console for progress.\n"
                "DO NOT disconnect the device during restore.",
            )
        except DeviceBridgeError as exc:
            QMessageBox.warning(self, "Restore Error", str(exc))

    def _open_dfu_wizard(self) -> None:
        wizard = DfuWizardDialog(self)
        wizard.exec()

    def closeEvent(self, event) -> None:
        self._monitor.stop()
        super().closeEvent(event)
