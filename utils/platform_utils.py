"""Windows-specific helpers."""

import sys


def is_windows() -> bool:
    return sys.platform == "win32"


def check_prerequisites() -> list[str]:
    """Return a list of missing prerequisite warnings."""
    warnings: list[str] = []

    try:
        import pymobiledevice3  # noqa: F401
    except ImportError:
        warnings.append("pymobiledevice3 not installed")

    try:
        import usb.core  # noqa: F401
    except ImportError:
        warnings.append("pyusb not installed — DFU/Recovery USB detection limited")

    if is_windows():
        import shutil

        if not shutil.which("irecovery") and not shutil.which("irecovery.exe"):
            warnings.append("irecovery not in PATH — recovery commands unavailable")

    return warnings
