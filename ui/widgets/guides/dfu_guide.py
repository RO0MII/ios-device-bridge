"""Step-by-step DFU Mode guide for iPhone 6s Plus."""

from PyQt6.QtWidgets import QFrame, QLabel, QListWidget, QVBoxLayout


IPHONE_6S_PLUS_DFU_STEPS = [
    "How to enter DFU Mode (screen stays black if successful):",
    "1. Connect your iPhone to the PC via USB.",
    "2. Press and hold Side (Power) + Home buttons together for 10 seconds.",
    "3. After 10 seconds, release the Side button — keep holding Home.",
    "4. Keep holding Home for another 5 seconds.",
    "5. Release Home. If the screen is black, DFU mode is active!",
    "6. The app will show a 'DFU Mode' indicator.",
    "Use the DFU Wizard (Dashboard) for exact button timing assistance.",
    "Apple logo or cable icon means exit and start over.",
]


class DfuGuidePanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Enter DFU Mode — iPhone 6s Plus")
        title.setObjectName("sectionTitle")

        subtitle = QLabel(
            "DFU mode allows low-level firmware interaction. "
            "The screen stays completely black when successful."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        steps = QListWidget()
        steps.addItems(IPHONE_6S_PLUS_DFU_STEPS)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(steps)
