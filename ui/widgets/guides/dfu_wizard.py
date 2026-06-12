"""Interactive DFU entry wizard with countdown timers for iPhone 6s Plus."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

DFU_WIZARD_STEPS = [
    {
        "title": "Step 1 — Connect USB",
        "instruction": "Connect your iPhone to the PC using a USB cable.",
        "duration_sec": 0,
        "action": "ready",
    },
    {
        "title": "Step 2 — Side + Home for 10 seconds",
        "instruction": "Press and hold both Side (Power) + Home buttons together.",
        "duration_sec": 10,
        "action": "hold_both",
    },
    {
        "title": "Step 3 — Release Side, keep Home",
        "instruction": "Release the Side button. Keep holding the Home button.",
        "duration_sec": 0,
        "action": "release_side",
    },
    {
        "title": "Step 4 — Hold Home for 5 seconds",
        "instruction": "Keep holding the Home button for 5 more seconds.",
        "duration_sec": 5,
        "action": "hold_home",
    },
    {
        "title": "Step 5 — Release Home",
        "instruction": "Release the Home button. If the screen stays black, DFU mode is active!",
        "duration_sec": 0,
        "action": "release_home",
    },
]


class DfuWizardDialog(QDialog):
    dfu_complete = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("DFU Mode Wizard — iPhone 6s Plus")
        self.setMinimumWidth(500)
        self._step_index = 0
        self._remaining = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        notice = QLabel(
            "DFU mode cannot be entered 100% automatically from PC due to "
            "Apple security. This wizard helps you get the exact button timing right."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #d29922; padding: 8px; font-weight: 500;")
        layout.addWidget(notice)

        panel = QFrame()
        panel.setObjectName("glassPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)

        self._step_title = QLabel()
        self._step_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        self._instruction = QLabel()
        self._instruction.setWordWrap(True)
        self._instruction.setObjectName("subtitle")

        self._countdown_label = QLabel("")
        self._countdown_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #58a6ff;")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)

        panel_layout.addWidget(self._step_title)
        panel_layout.addWidget(self._instruction)
        panel_layout.addWidget(self._countdown_label)
        panel_layout.addWidget(self._progress)
        layout.addWidget(panel)

        buttons = QHBoxLayout()
        self._prev_btn = QPushButton("← Previous")
        self._next_btn = QPushButton("Next →")
        self._next_btn.setObjectName("primaryButton")
        self._start_timer_btn = QPushButton("Start Timer")
        self._done_btn = QPushButton("Complete")

        self._prev_btn.clicked.connect(self._go_prev)
        self._next_btn.clicked.connect(self._go_next)
        self._start_timer_btn.clicked.connect(self._start_timer)
        self._done_btn.clicked.connect(self._finish)

        buttons.addWidget(self._prev_btn)
        buttons.addStretch()
        buttons.addWidget(self._start_timer_btn)
        buttons.addWidget(self._next_btn)
        buttons.addWidget(self._done_btn)
        layout.addLayout(buttons)

        self._render_step()

    def _render_step(self) -> None:
        step = DFU_WIZARD_STEPS[self._step_index]
        total = len(DFU_WIZARD_STEPS)
        self._step_title.setText(f"{step['title']}  ({self._step_index + 1}/{total})")
        self._instruction.setText(step["instruction"])
        self._countdown_label.setText("")
        self._progress.setValue(0)
        self._progress.setMaximum(step["duration_sec"] if step["duration_sec"] else 1)

        self._prev_btn.setEnabled(self._step_index > 0)
        self._next_btn.setEnabled(self._step_index < total - 1)
        self._start_timer_btn.setEnabled(step["duration_sec"] > 0)
        self._done_btn.setVisible(self._step_index == total - 1)
        self._next_btn.setVisible(self._step_index < total - 1)

    def _start_timer(self) -> None:
        step = DFU_WIZARD_STEPS[self._step_index]
        if step["duration_sec"] <= 0:
            return
        self._remaining = step["duration_sec"]
        self._progress.setMaximum(self._remaining)
        self._progress.setValue(0)
        self._countdown_label.setText(str(self._remaining))
        self._start_timer_btn.setEnabled(False)
        self._timer.start()

    def _tick(self) -> None:
        self._remaining -= 1
        step = DFU_WIZARD_STEPS[self._step_index]
        elapsed = step["duration_sec"] - self._remaining
        self._progress.setValue(elapsed)

        if self._remaining > 0:
            self._countdown_label.setText(str(self._remaining))
        else:
            self._timer.stop()
            self._countdown_label.setText("--")
            self._countdown_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #3fb950;")
            self._start_timer_btn.setEnabled(True)
            if self._step_index < len(DFU_WIZARD_STEPS) - 1:
                QTimer.singleShot(800, self._go_next)

    def _go_prev(self) -> None:
        if self._step_index > 0:
            self._timer.stop()
            self._step_index -= 1
            self._countdown_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #58a6ff;")
            self._render_step()

    def _go_next(self) -> None:
        if self._step_index < len(DFU_WIZARD_STEPS) - 1:
            self._timer.stop()
            self._step_index += 1
            self._countdown_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #58a6ff;")
            self._render_step()

    def _finish(self) -> None:
        self.dfu_complete.emit()
        QMessageBox.information(
            self,
            "DFU Check",
            "Is the screen black? Check the app dashboard — "
            "if it shows 'DFU Mode' badge, you're in DFU!\n\n"
            "If you see the Apple logo or cable icon, start over.",
        )
        self.accept()
