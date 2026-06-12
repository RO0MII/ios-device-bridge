"""Device event history and activity log."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from core.event_logger import EventLogger


class EventLogPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        self._logger = EventLogger()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Device History & Event Log")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._clear_btn = QPushButton("Clear History")
        self._clear_btn.clicked.connect(self._clear_history)
        header.addWidget(self._clear_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_table)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Time", "Event", "Mode", "Model", "UDID"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._refresh_table)
        self._timer.start()

        self._refresh_table()

    def _refresh_table(self) -> None:
        events = self._logger.get_history()
        self._table.setRowCount(len(events))
        for i, e in enumerate(events):
            self._table.setItem(i, 0, QTableWidgetItem(str(e.get("timestamp", ""))))
            self._table.setItem(i, 1, QTableWidgetItem(str(e.get("event", ""))))
            self._table.setItem(i, 2, QTableWidgetItem(str(e.get("mode", ""))))
            self._table.setItem(i, 3, QTableWidgetItem(str(e.get("model", ""))))
            self._table.setItem(i, 4, QTableWidgetItem(str(e.get("udid", ""))))

    def _clear_history(self) -> None:
        self._logger.clear()
        self._refresh_table()

    def log_event(self, event: str, **kwargs) -> None:
        self._logger.log(event, **kwargs)
        self._refresh_table()
