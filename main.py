#!/usr/bin/env python3
"""
iOS Device Bridge — Windows 11 desktop utility for connected iOS devices.

Prerequisites (Windows):
  - Python 3.10+
  - Apple Mobile Device Support / iTunes (provides usbmuxd)
  - libimobiledevice tools (irecovery, ideviceinfo) for recovery/DFU
  - Zadig/libusb driver for USB enumeration (optional, for DFU detection)

Usage:
  python main.py
"""

import sys

from PyQt6.QtWidgets import QApplication

from config.settings import SETTINGS
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(SETTINGS.app_name)
    app.setOrganizationName(SETTINGS.organization)
    app.setStyle("Fusion")  # Consistent cross-platform base; themed via QSS

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
