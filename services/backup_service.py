"""Device backup and restore operations."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Optional

from core.exceptions import DeviceBridgeError, DeviceNotFoundError
from core.mode_detector import DeviceMode, detect_current_mode


class BackupService:
    def __init__(self) -> None:
        self._backup_dir = Path.home() / "iOSDeviceBridge" / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def list_backups(self) -> list[dict[str, Any]]:
        results = []
        for d in sorted(self._backup_dir.iterdir()):
            if d.is_dir():
            # Try to read manifest
                manifest = d / "Manifest.plist"
                info = {
                    "name": d.name,
                    "path": str(d),
                    "size": sum(f.stat().st_size for f in d.rglob("*") if f.is_file()),
                    "date": d.stat().st_mtime,
                    "has_manifest": manifest.exists(),
                }
                info["size_gb"] = f"{info['size'] / (1024**3):.2f} GB"
                results.append(info)
        return sorted(results, key=lambda x: x["date"], reverse=True)

    def create_backup(self, progress_cb=None) -> str:
        mode, _ = detect_current_mode()
        if mode != DeviceMode.NORMAL:
            raise DeviceNotFoundError("Device must be in normal mode with Trust established.")

        import pymobiledevice3.lockdown as lockdown
        ld = lockdown.create_using_usbmux()
        from pymobiledevice3.services.mobile_backup import MobileBackupService
        backup = MobileBackupService(ld)
        backup_name = f"backup_{int(__import__('time').time())}"
        backup_path = str(self._backup_dir / backup_name)
        backup.backup(backup_path)
        return backup_path

    def restore_backup(self, backup_path: str) -> None:
        mode, _ = detect_current_mode()
        if mode != DeviceMode.NORMAL:
            raise DeviceNotFoundError("Device must be in normal mode with Trust established.")

        import pymobiledevice3.lockdown as lockdown
        ld = lockdown.create_using_usbmux()
        from pymobiledevice3.services.mobile_backup import MobileBackupService
        backup = MobileBackupService(ld)
        backup.restore(backup_path)

    def get_backup_size(self) -> int:
        total = sum(f.stat().st_size for f in self._backup_dir.rglob("*") if f.is_file())
        return total
