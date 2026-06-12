"""Custom exceptions for device communication."""


class DeviceBridgeError(Exception):
    """Base exception for all device bridge errors."""


class DeviceNotFoundError(DeviceBridgeError):
    """Raised when no iOS device is connected."""


class DeviceLockedError(DeviceBridgeError):
    """Raised when the device is locked and requires unlock."""


class PairingRequiredError(DeviceBridgeError):
    """Raised when the device requires trust/pairing confirmation."""


class RecoveryCommandError(DeviceBridgeError):
    """Raised when a recovery-mode command fails."""
