"""Device information table panel with comprehensive device properties."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.device_manager import DeviceManager, DeviceSnapshot
from core.exceptions import DeviceBridgeError


class DeviceInfoPanel(QFrame):
    def __init__(self, device_manager: DeviceManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = device_manager
        self.setObjectName("glassPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        header = QHBoxLayout()
        title = QLabel("Device Properties")
        title.setObjectName("sectionTitle")
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("accentButton")
        self._refresh_btn.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._refresh_btn)

        self._status = QLabel("Connect your iPhone to view device properties.")
        self._status.setObjectName("subtitle")
        self._status.setWordWrap(True)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Property", "Value"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        layout.addLayout(header)
        layout.addWidget(self._status)
        layout.addWidget(self._table)

    def refresh(self) -> None:
        try:
            snapshot = self._manager.get_snapshot()
            self._render_snapshot(snapshot)
        except DeviceBridgeError as exc:
            self._status.setText(str(exc))
            self._table.setRowCount(0)

    def _render_snapshot(self, snapshot: DeviceSnapshot) -> None:
        if snapshot.error_code and not snapshot.info:
            self._status.setText(snapshot.connection_message)
            self._table.setRowCount(0)
            return

        if snapshot.error_code and snapshot.info:
            self._status.setText(
                f"{snapshot.connection_message} · USB details below"
            )
        elif not snapshot.info:
            self._status.setText(snapshot.connection_message or "No data available.")
            self._table.setRowCount(0)
            return

        self._status.setText(f"Showing properties · {snapshot.mode.label}")
        self._table.setRowCount(len(snapshot.info))

        for row, (key, value) in enumerate(snapshot.info.items()):
            self._table.setItem(row, 0, QTableWidgetItem(key))
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, item)
