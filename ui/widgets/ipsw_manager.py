"""IPSW firmware downloader and manager."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QMessageBox,
)

import config.settings as cfg
from services.ipsw_service import IPSWInfo, IPSWService


IDENTIFIER_LIST = [
    "iPhone5,1", "iPhone5,2", "iPhone6,1", "iPhone6,2",
    "iPhone7,1", "iPhone7,2", "iPhone8,1", "iPhone8,2",
    "iPhone8,4", "iPhone9,1", "iPhone9,3", "iPhone9,2", "iPhone9,4",
    "iPhone10,1", "iPhone10,4", "iPhone10,2", "iPhone10,5",
    "iPhone10,3", "iPhone10,6",
    "iPhone11,2", "iPhone11,4", "iPhone11,6", "iPhone11,8",
    "iPhone12,1", "iPhone12,3", "iPhone12,5", "iPhone12,8",
    "iPhone13,1", "iPhone13,2", "iPhone13,3", "iPhone13,4",
    "iPhone14,2", "iPhone14,3", "iPhone14,4", "iPhone14,5",
    "iPhone14,6", "iPhone14,7", "iPhone14,8",
    "iPhone15,2", "iPhone15,3", "iPhone15,4", "iPhone15,5",
    "iPhone16,1", "iPhone16,2",
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4", "iPhone17,5",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4", "iPhone18,5",
]


class DownloadThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, service: IPSWService, ipsw: IPSWInfo, dest: str) -> None:
        super().__init__()
        self._service = service
        self._ipsw = ipsw
        self._dest = dest

    def run(self) -> None:
        try:
            path = self._service.download_progress(self._ipsw, self._dest, self.progress.emit)
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))


class FetchThread(QThread):
    data_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, service: IPSWService, identifier: str) -> None:
        super().__init__()
        self._service = service
        self._identifier = identifier

    def run(self) -> None:
        try:
            firmwares = self._service.fetch_firmwares(self._identifier)
            self.data_ready.emit(firmwares)
        except Exception as e:
            self.error.emit(str(e))


class IPSWManagerPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        self._service = IPSWService()
        self._firmwares: list[IPSWInfo] = []
        self._download_thread: DownloadThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("IPSW Firmware Manager")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        selector = QHBoxLayout()

        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.setPlaceholderText("Type model identifier...")
        for ident in IDENTIFIER_LIST:
            self._model_combo.addItem(ident)
        selector.addWidget(self._model_combo, 1)

        self._fetch_btn = QPushButton("Fetch Signed IPSW")
        self._fetch_btn.clicked.connect(self._fetch_firmwares)
        selector.addWidget(self._fetch_btn)

        layout.addLayout(selector)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Version", "Build", "Size", "Released", "Status"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        layout.addWidget(self._progress)

        actions = QHBoxLayout()

        self._download_btn = QPushButton("Download Selected")
        self._download_btn.setObjectName("accentButton")
        self._download_btn.clicked.connect(self._download_selected)
        actions.addWidget(self._download_btn)

        self._verify_btn = QPushButton("Verify Local")
        self._verify_btn.clicked.connect(self._verify_local)
        actions.addWidget(self._verify_btn)

        self._refresh_local_btn = QPushButton("List Local")
        self._refresh_local_btn.clicked.connect(self._list_local)
        actions.addWidget(self._refresh_local_btn)

        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()

    def _fetch_firmwares(self) -> None:
        identifier = self._model_combo.currentText().strip()
        if not identifier:
            QMessageBox.warning(self, "No Model", "Enter or select a model identifier.")
            return

        self._fetch_btn.setEnabled(False)
        self._fetch_btn.setText("Fetching...")

        self._table.setRowCount(0)

        thread = FetchThread(self._service, identifier)
        thread.data_ready.connect(self._on_firmwares)
        thread.error.connect(lambda e: self._show_error(e))
        thread.finished.connect(lambda: self._fetch_btn.setEnabled(True))
        thread.finished.connect(lambda: self._fetch_btn.setText("Fetch Signed IPSW"))
        thread.start()

    def _on_firmwares(self, firmwares: list[IPSWInfo]) -> None:
        self._firmwares = firmwares
        self._table.setRowCount(len(firmwares))
        for i, fw in enumerate(firmwares):
            self._table.setItem(i, 0, QTableWidgetItem(fw.version))
            self._table.setItem(i, 1, QTableWidgetItem(fw.buildid))
            self._table.setItem(i, 2, QTableWidgetItem(fw.size_mb))
            self._table.setItem(i, 3, QTableWidgetItem(fw.releasedate[:10]))
            local = self._is_local(fw)
            self._table.setItem(i, 4, QTableWidgetItem("Downloaded" if local else "Available"))

        if not firmwares:
            QMessageBox.information(self, "No Firmwares", "No signed firmwares found for this model.")

    def _is_local(self, fw: IPSWInfo) -> bool:
        ipsw_dir = Path(cfg.IPSW_DOWNLOAD_DIR)
        target = ipsw_dir / fw.filename
        return target.exists()

    def _download_selected(self) -> None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._firmwares):
            QMessageBox.warning(self, "No Selection", "Select a firmware row first.")
            return

        ipsw = self._firmwares[row]
        if self._is_local(ipsw):
            QMessageBox.information(self, "Already Downloaded", f"{ipsw.filename} is already in {cfg.IPSW_DOWNLOAD_DIR}")
            return

        dest = cfg.IPSW_DOWNLOAD_DIR
        os.makedirs(dest, exist_ok=True)

        self._download_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        thread = DownloadThread(self._service, ipsw, dest)
        thread.progress.connect(lambda d, t: self._progress.setValue(int(d / t * 100)))
        thread.finished.connect(self._on_download_finished)
        thread.error.connect(lambda e: self._show_error(e))
        thread.finished.connect(lambda: self._download_btn.setEnabled(True))
        thread.start()

    def _on_download_finished(self, path: str) -> None:
        self._progress.setValue(100)
        self._progress.setVisible(False)
        self._refresh_table()
        QMessageBox.information(self, "Download Complete", f"Saved to:\n{path}")

    def _verify_local(self) -> None:
        local = self._service.list_local_ipsw()
        if not local:
            QMessageBox.information(self, "No Files", "No IPSW files found locally.")
            return
        text = "\n".join(f"{f['name']}  ({f['size_gb']})" for f in local)
        QMessageBox.information(self, f"Local IPSW ({len(local)})", text)

    def _list_local(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        for i in range(self._table.rowCount()):
            if i < len(self._firmwares):
                local = self._is_local(self._firmwares[i])
                self._table.item(i, 4).setText("Downloaded" if local else "Available")

    def _show_error(self, msg: str) -> None:
        QMessageBox.warning(self, "Error", msg)
