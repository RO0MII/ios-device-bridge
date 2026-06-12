"""Fetch readable device properties via pymobiledevice3."""

from __future__ import annotations

from typing import Any

from core.exceptions import DeviceLockedError, PairingRequiredError


MODEL_NAME_MAP = {
    "iPhone5,1": "iPhone 5 (GSM)",
    "iPhone5,2": "iPhone 5 (GSM+CDMA)",
    "iPhone5,3": "iPhone 5c (GSM)",
    "iPhone5,4": "iPhone 5c (Global)",
    "iPhone6,1": "iPhone 5s (GSM)",
    "iPhone6,2": "iPhone 5s (Global)",
    "iPhone7,1": "iPhone 6 Plus",
    "iPhone7,2": "iPhone 6",
    "iPhone8,1": "iPhone 6s",
    "iPhone8,2": "iPhone 6s Plus",
    "iPhone8,4": "iPhone SE (1st gen)",
    "iPhone9,1": "iPhone 7",
    "iPhone9,2": "iPhone 7 Plus",
    "iPhone9,3": "iPhone 7",
    "iPhone9,4": "iPhone 7 Plus",
    "iPhone10,1": "iPhone 8",
    "iPhone10,2": "iPhone 8 Plus",
    "iPhone10,3": "iPhone X",
    "iPhone10,4": "iPhone 8",
    "iPhone10,5": "iPhone 8 Plus",
    "iPhone10,6": "iPhone X",
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max",
    "iPhone11,8": "iPhone XR",
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max",
    "iPhone12,8": "iPhone SE (2nd gen)",
    "iPhone13,1": "iPhone 12 mini",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone14,4": "iPhone 13 mini",
    "iPhone14,5": "iPhone 13",
    "iPhone14,6": "iPhone SE (3rd gen)",
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    "iPhone17,5": "iPhone 16e",
    "iPhone18,1": "iPhone 17 Pro",
    "iPhone18,2": "iPhone 17 Pro Max",
    "iPhone18,3": "iPhone 17",
    "iPhone18,4": "iPhone Air",
    "iPhone18,5": "iPhone 17e",
}


class DeviceInfoService:
    """Reads lockdown and diagnostics data from a paired iOS device."""

    PROPERTY_MAP = {
        "DeviceName": "Device Name",
        "ProductType": "Model Code",
        "ProductVersion": "iOS Version",
        "BuildVersion": "Build Version",
        "SerialNumber": "Serial Number",
        "UniqueDeviceID": "UDID",
        "InternationalMobileEquipmentIdentity": "IMEI",
        "CPUArchitecture": "CPU Architecture",
        "HardwareModel": "Hardware Model",
        "DeviceColor": "Color",
        "ActivationState": "Activation State",
        "BluetoothAddress": "Bluetooth Address",
        "WiFiAddress": "Wi-Fi Address",
        "BasebandVersion": "Baseband Version",
        "BasebandBootloaderVersion": "Baseband Bootloader",
        "FirmwareVersion": "Firmware Version",
        "RegionCode": "Region",
        "RegionInfo": "Region Info",
        "TimeZone": "Time Zone",
        "TelephonyCarrier": "Carrier",
        "EthernetAddress": "Ethernet Address",
        "MLBSerialNumber": "MLB Serial",
        "ModelNumber": "Model Number",
        "PlatformVersion": "Platform Version",
        "ProductName": "Product Name",
        "ReleaseMode": "Release Mode",
        "UniqueChipID": "Chip ID",
        "SupportedDeviceGroups": "Supported Groups",
        "BoardId": "Board ID",
        "ChipID": "Chip ID",
        "SecurityDomain": "Security Domain",
        "PasswordProtected": "Passcode Enabled",
    }

    def fetch_all(self) -> dict[str, Any]:
        lockdown = self._connect()
        info: dict[str, Any] = {}

        for raw_key, label in self.PROPERTY_MAP.items():
            try:
                value = lockdown.get_value(key=raw_key)
                if value is not None and value != "":
                    info[label] = str(value)
            except Exception:
                continue

        info.update(self._fetch_battery_info(lockdown))
        info.update(self._fetch_model_name(lockdown))
        info.update(self._fetch_storage_info(lockdown))
        return info

    def _connect(self):
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
        except ImportError as exc:
            raise PairingRequiredError(
                "pymobiledevice3 is not installed. Run: pip install pymobiledevice3"
            ) from exc

        try:
            return create_using_usbmux()
        except Exception as exc:
            exc_name = type(exc).__name__
            if exc_name == "NotPairedError":
                raise PairingRequiredError(
                    "Pairing required. Unlock the device and tap 'Trust This Computer'."
                ) from exc
            if exc_name in ("DeviceLockedError", "PasswordRequiredError"):
                raise DeviceLockedError(
                    "Device is locked. Unlock your iPhone and try again."
                ) from exc
            raise

    def _fetch_model_name(self, lockdown) -> dict[str, str]:
        try:
            product_type = lockdown.get_value(key="ProductType", default="")
            friendly = MODEL_NAME_MAP.get(product_type, product_type)
            return {"Model": friendly}
        except Exception:
            return {}

    def _fetch_battery_info(self, lockdown) -> dict[str, str]:
        results: dict[str, str] = {}
        try:
            from pymobiledevice3.services.diagnostics import DiagnosticsService

            diag = DiagnosticsService(lockdown)
            battery = diag.get_battery()
            if battery:
                design_capacity = battery.get("DesignCapacity")
                full_capacity = battery.get("FullChargeCapacity") or battery.get("AppleRawMaxCapacity")
                cycle_count = battery.get("CycleCount")

                if design_capacity and full_capacity:
                    health_pct = round((int(full_capacity) / int(design_capacity)) * 100, 1)
                    results["Battery Health"] = health_pct
                if cycle_count is not None:
                    results["Battery Cycle Count"] = str(cycle_count)
        except Exception:
            results["Battery Health"] = "Unavailable"
        return results

    def _fetch_storage_info(self, lockdown) -> dict[str, str]:
        results: dict[str, str] = {}
        try:
            from pymobiledevice3.services.diagnostics import DiagnosticsService

            diag = DiagnosticsService(lockdown)
            storage = diag.get_storage()
            if storage:
                total = int(storage.get("TotalDiskCapacity", [0])[0]) / (1024**3)
                available = int(storage.get("TotalDiskAvailableCapacity", [0])[0]) / (1024**3)
                used = total - available
                results["Storage"] = f"{used:.1f} GB / {total:.1f} GB"
                results["Storage Available"] = f"{available:.1f} GB"
        except Exception:
            pass
        return results
