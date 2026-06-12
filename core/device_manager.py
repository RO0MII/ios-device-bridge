"""High-level device operations facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import subprocess

from core.event_logger import EventLogger
from core.exceptions import (
    DeviceLockedError,
    DeviceNotFoundError,
    PairingRequiredError,
    RecoveryCommandError,
)
from core.mode_detector import DeviceMode, detect_current_mode
from services.backup_service import BackupService
from services.device_info_service import DeviceInfoService
from services.ipsw_service import IPSWService
from services.recovery_service import RecoveryService
from services.unpaired_service import UnpairedAccessService


@dataclass
class DeviceSnapshot:
    mode: DeviceMode
    info: dict[str, Any] = field(default_factory=dict)
    connection_message: str = ""
    error_code: Optional[str] = None


class DeviceManager:
    """Coordinates info retrieval and recovery commands."""

    def __init__(self) -> None:
        self._info_service = DeviceInfoService()
        self._recovery_service = RecoveryService()
        self._unpaired_service = UnpairedAccessService()
        self._backup_service = BackupService()
        self._ipsw_service = IPSWService()
        self._event_logger = EventLogger()

    def get_event_logger(self) -> EventLogger:
        return self._event_logger

    def get_ipsw_service(self) -> IPSWService:
        return self._ipsw_service

    def get_backup_service(self) -> BackupService:
        return self._backup_service

    def get_snapshot(self) -> DeviceSnapshot:
        mode, _ = detect_current_mode()
        if mode == DeviceMode.DISCONNECTED:
            raise DeviceNotFoundError("No iOS device connected.")

        if mode == DeviceMode.NORMAL:
            try:
                info = self._info_service.fetch_all()
                return DeviceSnapshot(mode=mode, info=info)
            except PairingRequiredError as exc:
                return DeviceSnapshot(
                    mode=mode,
                    connection_message=str(exc),
                    error_code="PAIRING_REQUIRED",
                )
            except DeviceLockedError as exc:
                return DeviceSnapshot(
                    mode=mode,
                    connection_message=str(exc),
                    error_code="DEVICE_LOCKED",
                )

        if mode in (DeviceMode.RECOVERY, DeviceMode.DFU):
            info = self._unpaired_service.fetch_usb_info()
            return DeviceSnapshot(
                mode=mode,
                info={k: str(v) for k, v in info.items() if k not in ("status", "access_level")},
                connection_message="Full USB access granted without Trust.",
            )

        info = self._unpaired_service.fetch_usb_info()
        return DeviceSnapshot(
            mode=mode,
            info={k: str(v) for k, v in info.items() if k not in ("status", "access_level")},
            connection_message="USB detected — enter Recovery or DFU mode for full access.",
            error_code="PAIRING_REQUIRED",
        )

    def get_unpaired_info(self) -> dict:
        return self._unpaired_service.fetch_usb_info()

    def exit_recovery_mode(self) -> None:
        mode, _ = detect_current_mode()
        if mode != DeviceMode.RECOVERY:
            raise RecoveryCommandError("Device is not in Recovery Mode.")
        self._recovery_service.exit_recovery()
        self._event_logger.log_action("Exit Recovery Mode")

    def reboot_to_recovery(self) -> None:
        self._recovery_service.enter_recovery()
        self._event_logger.log_action("Enter Recovery Mode")

    def force_dfu_recovery(self) -> None:
        mode, _ = detect_current_mode()
        if mode == DeviceMode.DISCONNECTED:
            raise DeviceNotFoundError("No iOS device connected.")
        if mode == DeviceMode.RECOVERY:
            raise RecoveryCommandError("Device is already in Recovery Mode.")
        self._recovery_service.enter_recovery()
        self._event_logger.log_action("Force Recovery Mode")

    def restore_device(self, ipsw_path: str) -> subprocess.Popen:
        mode, _ = detect_current_mode()
        if mode not in (DeviceMode.RECOVERY, DeviceMode.DFU):
            raise RecoveryCommandError("Device must be in Recovery or DFU mode to restore.")
        return self._recovery_service.restore(ipsw_path)

    def reboot_device(self) -> None:
        mode, _ = detect_current_mode()
        if mode not in (DeviceMode.RECOVERY, DeviceMode.DFU):
            raise RecoveryCommandError("Device must be in Recovery or DFU mode to reboot.")
        self._recovery_service.reboot()

    def get_device_ecid(self) -> str:
        return self._recovery_service.get_ecid()
