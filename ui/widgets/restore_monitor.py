"""Live restore log viewer with real-time output from idevicerestore."""

from __future__ import annotations

from PyQt6.QtCore import QProcess, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar,
    QPushButton, QVBoxLayout, QFileDialog, QMessageBox,
)
from PyQt6.QtGui import QColor, QTextCursor

import config.settings as cfg


class RestoreMonitorPanel(QFrame):
    restore_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Restore Monitor")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._clear_btn = QPushButton("Clear Log")
        self._clear_btn.clicked.connect(self._clear_log)
        header.addWidget(self._clear_btn)
        layout.addLayout(header)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(5000)
        self._log.setStyleSheet("""
            QPlainTextEdit {
                background: rgba(0,0,0,0.3);
                color: #f0f0f0;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                padding: 12px;
                font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self._log, 1)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        layout.addWidget(self._progress)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self._start_btn = QPushButton("Start Restore")
        self._start_btn.setObjectName("dangerButton")
        self._start_btn.clicked.connect(self._start_restore)
        actions.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_restore)
        actions.addWidget(self._stop_btn)

        self._ipsw_label = QLabel("No IPSW selected")
        self._ipsw_label.setObjectName("subtitle")
        actions.addWidget(self._ipsw_label)
        actions.addStretch()

        self._select_btn = QPushButton("Select IPSW...")
        self._select_btn.clicked.connect(self._select_ipsw)
        actions.addWidget(self._select_btn)

        layout.addLayout(actions)

        self._process: QProcess | None = None
        self._ipsw_path: str = ""

    def _log_message(self, msg: str, level: str = "info") -> None:
        colors = {"error": "#ff453a", "warn": "#ff9f0a", "info": "#f0f0f0", "ok": "#30d158"}
        color = colors.get(level, "#f0f0f0")
        self._log.appendHtml(f'<span style="color:{color}">{msg}</span>')
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log.setTextCursor(cursor)

    def _clear_log(self) -> None:
        self._log.clear()

    def _select_ipsw(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select IPSW Firmware", cfg.IPSW_DOWNLOAD_DIR,
            "IPSW Files (*.ipsw);;All Files (*.*)",
        )
        if path:
            self._ipsw_path = path
            self._ipsw_label.setText(path.split("/")[-1].split("\\")[-1])

    def _start_restore(self) -> None:
        if not self._ipsw_path:
            QMessageBox.warning(self, "No IPSW", "Select an IPSW file first.")
            return

        from core.mode_detector import DeviceMode, detect_current_mode
        mode, _ = detect_current_mode()
        if mode not in (DeviceMode.RECOVERY, DeviceMode.DFU):
            QMessageBox.warning(
                self, "Wrong Mode",
                "Device must be in Recovery or DFU mode to restore.",
            )
            return

        reply = QMessageBox.warning(
            self, "Confirm Restore",
            "This will ERASE all data on your iPhone.\n\n"
            f"IPSW: {self._ipsw_path}\n\n"
            "This cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._log_message("Starting restore process...", "info")
        self._log_message(f"IPSW: {self._ipsw_path}", "info")
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._select_btn.setEnabled(False)

        import shutil
        tool = shutil.which("idevicerestore") or shutil.which("idevicerestore.exe")
        if not tool:
            self._log_message("idevicerestore not found!", "error")
            self._reset_ui()
            return

        self._process = QProcess()
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.finished.connect(self._process_finished)
        self._process.started.connect(lambda: self._log_message("Process started.", "ok"))
        self._process.start(tool, ["-y", self._ipsw_path])

    def _read_output(self) -> None:
        if not self._process:
            return
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if "error" in lower or "fail" in lower or "abort" in lower:
                self._log_message(line, "error")
            elif "warning" in lower or "skip" in lower:
                self._log_message(line, "warn")
            elif "done" in lower or "success" in lower or "complete" in lower:
                self._log_message(line, "ok")
            else:
                self._log_message(line, "info")

            # Try to extract progress percentage
            import re
            m = re.search(r"(\d+)%", line)
            if m:
                self._progress.setValue(int(m.group(1)))

    def _process_finished(self, exit_code: int, exit_status) -> None:
        self._log_message(f"Restore process finished (exit code: {exit_code})", "ok" if exit_code == 0 else "error")
        self._progress.setValue(100 if exit_code == 0 else 0)
        self._reset_ui()
        self.restore_finished.emit(exit_code == 0, f"Exit code: {exit_code}")

    def _stop_restore(self) -> None:
        if self._process and self._process.state() == QProcess.ProcessState.Running:
            self._process.kill()
            self._log_message("Restore terminated by user.", "warn")
        self._reset_ui()

    def _reset_ui(self) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._select_btn.setEnabled(True)
        QTimer.singleShot(3000, lambda: self._progress.setVisible(False))
