"""Application-wide configuration."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "iOS Device Bridge"
    app_name_si: str = "iPhone USB Manager"
    app_version: str = "1.0.0"
    organization: str = "iOS Device Bridge"
    poll_interval_ms: int = 1500
    device_info_refresh_ms: int = 5000
    window_min_width: int = 1100
    window_min_height: int = 720
    default_theme: str = "dark"


current_theme: str = "glass"

AVAILABLE_THEMES = {
    "glass": "Glass",
    "dark": "Dark (Blue)",
    "bw": "Black & White",
}


@dataclass(frozen=True)
class ThemeColors:
    background: str = "#0d1117"
    surface: str = "#161b22"
    surface_elevated: str = "#1c2128"
    border: str = "#30363d"
    accent: str = "#58a6ff"
    accent_hover: str = "#79b8ff"
    success: str = "#3fb950"
    warning: str = "#d29922"
    danger: str = "#f85149"
    text_primary: str = "#e6edf3"
    text_secondary: str = "#8b949e"
    glass_overlay: str = "rgba(22, 27, 34, 0.72)"


# Restore configuration
IPSW_FALLBACK_URL: str = "https://ipsw.me/"
IPSW_DOWNLOAD_DIR: str = ""

# Apple USB identifiers used for mode detection
APPLE_VENDOR_ID = 0x05AC
NORMAL_MODE_PRODUCT_IDS = {
    0x12A8,  # iPhone (normal)
    0x12AA,  # iPhone (paired)
}
RECOVERY_MODE_PRODUCT_ID = 0x1281
DFU_MODE_PRODUCT_ID = 0x1227

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = PROJECT_ROOT / "ui" / "resources"

SETTINGS = AppSettings()
COLORS = ThemeColors()
