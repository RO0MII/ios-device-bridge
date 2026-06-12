"""Step-by-step Recovery Mode guide for iPhone 6s Plus."""

from PyQt6.QtWidgets import QFrame, QLabel, QListWidget, QVBoxLayout


IPHONE_6S_PLUS_RECOVERY_STEPS = [
    "How to enter Recovery Mode (works even with a broken screen):",
    "1. Fully power off your iPhone.",
    "2. Connect the USB cable to your PC (not to the iPhone yet).",
    "3. Press and hold the Side (Power) button.",
    "4. While holding Side, connect the USB cable to your iPhone.",
    "5. Keep holding Side until the recovery screen (cable + iTunes icon) appears.",
    "6. Release the Side button. The app will show 'Recovery Mode'.",
    "No Trust required — full access in Recovery Mode!",
    "Tip: If you see the Apple logo, start over from step 1.",
]


class RecoveryGuidePanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Enter Recovery Mode — iPhone 6s Plus")
        title.setObjectName("sectionTitle")

        subtitle = QLabel(
            "Use these hardware button steps when the device won't boot normally "
            "or when Trust is unavailable."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        steps = QListWidget()
        steps.addItems(IPHONE_6S_PLUS_RECOVERY_STEPS)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(steps)
