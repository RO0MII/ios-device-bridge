"""Fetch device data without lockdown pairing (Recovery/DFU/USB only)."""

from __future__ import annotations

from typing import Any

from config.settings import APPLE_VENDOR_ID
from core.mode_detector import (
    DeviceMode,
    UsbDeviceDescriptor,
    detect_current_mode,
    mode_from_usb_descriptor,
    scan_usb_for_apple_devices,
)
from services.recovery_service import RecoveryService

PRODUCT_ID_LABELS = {
    0x12A8: "iPhone — Normal (Unpaired)",
    0x12AA: "iPhone — Normal (Paired)",
    0x1281: "iPhone — Recovery Mode",
    0x1227: "iPhone — DFU Mode",
}


class UnpairedAccessService:
    """
    Access pathway that does NOT require 'Trust This Computer'.
    Works in Recovery/DFU via irecovery, and USB-level detection in all modes.
    """

    def __init__(self) -> None:
        self._recovery = RecoveryService()

    def fetch_usb_info(self) -> dict[str, Any]:
        mode, descriptor = detect_current_mode()
        if mode == DeviceMode.DISCONNECTED:
            return {"status": "disconnected"}

        info: dict[str, Any] = {
            "status": "connected",
            "mode": mode.label,
            "trust_required": mode == DeviceMode.NORMAL,
            "access_level": self._access_level(mode),
        }

        if descriptor:
            info.update(self._describe_usb(descriptor))

        if mode in (DeviceMode.RECOVERY, DeviceMode.DFU):
            info.update(self._recovery.get_recovery_info())
        elif mode == DeviceMode.NORMAL and not info.get("trust_required"):
            pass
        elif mode == DeviceMode.NORMAL:
            info["pairing_note"] = (
                "Normal mode — full data not available without Trust. "
                "Enter Recovery or DFU mode for full access."
            )

        return info

    def fetch_all_apple_devices(self) -> list[dict[str, str]]:
        devices = scan_usb_for_apple_devices()
        results = []
        for d in devices:
            mode = mode_from_usb_descriptor(d)
            entry = {
                "Vendor ID": f"0x{d.vendor_id:04X}",
                "Product ID": f"0x{d.product_id:04X}",
                "Mode": mode.label,
                "Type": PRODUCT_ID_LABELS.get(d.product_id, "Unknown Apple Device"),
            }
            if d.serial_number:
                entry["USB Serial"] = d.serial_number
            results.append(entry)
        return results

    def _describe_usb(self, descriptor: UsbDeviceDescriptor) -> dict[str, str]:
        return {
            "Vendor ID": f"0x{descriptor.vendor_id:04X}",
            "Product ID": f"0x{descriptor.product_id:04X}",
            "Device Type": PRODUCT_ID_LABELS.get(
                descriptor.product_id, "Apple iOS Device"
            ),
            "USB Serial": descriptor.serial_number or "—",
        }

    @staticmethod
    def _access_level(mode: DeviceMode) -> str:
        levels = {
            DeviceMode.DISCONNECTED: "none",
            DeviceMode.NORMAL: "usb_only",
            DeviceMode.RECOVERY: "full_recovery",
            DeviceMode.DFU: "full_dfu",
            DeviceMode.UNKNOWN: "limited",
        }
        return levels.get(mode, "limited")
