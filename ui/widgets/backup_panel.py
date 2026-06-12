"""Device backup and restore panel."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)

from services.backup_service import BackupService


class BackupThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, service: BackupService) -> None:
        super().__init__()
        self._service = service

    def run(self) -> None:
        try:
            path = self._service.create_backup()
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))


class BackupPanel(QFrame):
    def __init__(self, backup_service: BackupService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        self._service = backup_service or BackupService()
        self._backup_thread: BackupThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Backup & Restore")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        subtitle = QLabel("Create full device backups or restore from previous backups.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self._backup_btn = QPushButton("Create Backup")
        self._backup_btn.setObjectName("primaryButton")
        self._backup_btn.clicked.connect(self._create_backup)
        actions.addWidget(self._backup_btn)

        self._restore_btn = QPushButton("Restore Backup")
        self._restore_btn.setObjectName("dangerButton")
        self._restore_btn.clicked.connect(self._restore_backup)
        actions.addWidget(self._restore_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_table)
        actions.addWidget(self._refresh_btn)

        actions.addStretch()
        layout.addLayout(actions)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Name", "Size", "Date", "Manifest"])
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        import time
        self._refresh_table()

    def _refresh_table(self) -> None:
        import time
        backups = self._service.list_backups()
        self._table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            self._table.setItem(i, 0, QTableWidgetItem(b["name"]))
            self._table.setItem(i, 1, QTableWidgetItem(b.get("size_gb", "0 GB")))
            self._table.setItem(i, 2, QTableWidgetItem(
                time.strftime("%Y-%m-%d %H:%M", time.localtime(b["date"]))
            ))
            self._table.setItem(i, 3, QTableWidgetItem("Yes" if b["has_manifest"] else "No"))

    def _create_backup(self) -> None:
        self._backup_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)

        thread = BackupThread(self._service)
        thread.finished.connect(self._on_backup_finished)
        thread.error.connect(self._on_backup_error)
        thread.start()
        self._backup_thread = thread

    def _on_backup_finished(self, path: str) -> None:
        self._progress.setVisible(False)
        self._backup_btn.setEnabled(True)
        self._refresh_table()
        QMessageBox.information(self, "Backup Complete", f"Saved to:\n{path}")

    def _on_backup_error(self, msg: str) -> None:
        self._progress.setVisible(False)
        self._backup_btn.setEnabled(True)
        QMessageBox.warning(self, "Backup Failed", msg)

    def _restore_backup(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a backup row first.")
            return

        backups = self._service.list_backups()
        if row >= len(backups):
            return

        backup = backups[row]
        reply = QMessageBox.warning(
            self, "Restore Backup",
            "This will overwrite data on your iPhone.\n\n"
            f"Backup: {backup['name']}\n"
            f"Size: {backup.get('size_gb', '0 GB')}\n\n"
            "This cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.restore_backup(backup["path"])
            QMessageBox.information(self, "Restore Started", "Backup restore has begun.")
        except Exception as e:
            QMessageBox.warning(self, "Restore Failed", str(e))
