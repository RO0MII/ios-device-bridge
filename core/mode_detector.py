"""Detect iOS device connection mode: Normal, Recovery, or DFU."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from config.settings import (
    APPLE_VENDOR_ID,
    DFU_MODE_PRODUCT_ID,
    NORMAL_MODE_PRODUCT_IDS,
    RECOVERY_MODE_PRODUCT_ID,
)


class DeviceMode(str, Enum):
    DISCONNECTED = "disconnected"
    NORMAL = "normal"
    RECOVERY = "recovery"
    DFU = "dfu"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        return {
            DeviceMode.DISCONNECTED: "Disconnected",
            DeviceMode.NORMAL: "Normal Mode",
            DeviceMode.RECOVERY: "Recovery Mode",
            DeviceMode.DFU: "DFU Mode",
            DeviceMode.UNKNOWN: "Unknown",
        }[self]

    @property
    def badge_color(self) -> str:
        return {
            DeviceMode.DISCONNECTED: "#6e7681",
            DeviceMode.NORMAL: "#3fb950",
            DeviceMode.RECOVERY: "#d29922",
            DeviceMode.DFU: "#f85149",
            DeviceMode.UNKNOWN: "#8b949e",
        }[self]


@dataclass
class UsbDeviceDescriptor:
    vendor_id: int
    product_id: int
    serial_number: Optional[str] = None


def mode_from_usb_descriptor(descriptor: UsbDeviceDescriptor) -> DeviceMode:
    """Map Apple USB vendor/product IDs to a device mode."""
    if descriptor.vendor_id != APPLE_VENDOR_ID:
        return DeviceMode.UNKNOWN

    if descriptor.product_id == DFU_MODE_PRODUCT_ID:
        return DeviceMode.DFU
    if descriptor.product_id == RECOVERY_MODE_PRODUCT_ID:
        return DeviceMode.RECOVERY
    if descriptor.product_id in NORMAL_MODE_PRODUCT_IDS:
        return DeviceMode.NORMAL
    return DeviceMode.UNKNOWN


def scan_usb_for_apple_devices() -> list[UsbDeviceDescriptor]:
    """
    Enumerate connected USB devices and return Apple descriptors.
    Requires pyusb + libusb backend on Windows.
    """
    try:
        import usb.core
        import usb.util
    except ImportError:
        return []

    devices: list[UsbDeviceDescriptor] = []
    for dev in usb.core.find(find_all=True):
        try:
            if dev.idVendor != APPLE_VENDOR_ID:
                continue
            serial = None
            try:
                serial = usb.util.get_string(dev, dev.iSerialNumber) if dev.iSerialNumber else None
            except (usb.core.USBError, ValueError):
                serial = None
            devices.append(
                UsbDeviceDescriptor(
                    vendor_id=dev.idVendor,
                    product_id=dev.idProduct,
                    serial_number=serial,
                )
            )
        except (usb.core.USBError, AttributeError):
            continue
    return devices


def detect_current_mode() -> tuple[DeviceMode, Optional[UsbDeviceDescriptor]]:
    """
    Determine the active device mode using a layered detection strategy:
    1. USB product ID scan (fast, works for DFU/Recovery)
    2. pymobiledevice3 lockdown probe (confirms Normal mode + pairing)
    """
    apple_devices = scan_usb_for_apple_devices()

    # DFU and Recovery take priority — lockdown won't respond in those modes
    for descriptor in apple_devices:
        mode = mode_from_usb_descriptor(descriptor)
        if mode in (DeviceMode.DFU, DeviceMode.RECOVERY):
            return mode, descriptor

    # Attempt lockdown connection for normal mode
    try:
        from pymobiledevice3.lockdown import create_using_usbmux

        lockdown = create_using_usbmux()
        if lockdown:
            normal_descriptor = next(
                (d for d in apple_devices if mode_from_usb_descriptor(d) == DeviceMode.NORMAL),
                apple_devices[0] if apple_devices else None,
            )
            return DeviceMode.NORMAL, normal_descriptor
    except Exception:
        pass

    if apple_devices:
        descriptor = apple_devices[0]
        return mode_from_usb_descriptor(descriptor), descriptor

    return DeviceMode.DISCONNECTED, None
