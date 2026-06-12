#!/usr/bin/env python3
"""Build iOS Device Bridge as a standalone Windows .exe using PyInstaller.

Usage:
    python build.py              # Build .exe only
    python build.py --installer  # Build .exe + Inno Setup installer

Requirements:
    pip install pyinstaller
    (Optional for installer) Inno Setup: https://jrsoftware.org/isdl.php
"""

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
TOOLS_DIR = DIST_DIR / "tools"
SPEC_FILE = PROJECT_ROOT / "ios_device_bridge.spec"
APP_NAME = "iOSDeviceBridge"
VERSION = "1.0.0"

LIBIMOBILEDEVICE_URL = (
    "https://github.com/libimobiledevice-win32/imobiledevice-net/releases/"
    "download/v1.3.17/imobiledevice_1.3.17_win64.zip"
)

TOOLS_NEEDED = [
    "irecovery.exe",
    "idevicerestore.exe",
    "ideviceenterrecovery.exe",
    "libusb-1.0.dll",
    "libplist-2.0.dll",
    "libimobiledevice-1.0.dll",
    "libusbmuxd-2.0.dll",
    "libcurl.dll",
    "libssl-1_1-x64.dll",
    "libcrypto-1_1-x64.dll",
    "zlib1.dll",
    "libiconv-2.dll",
    "libintl-8.dll",
    "libpcre2-8-0.dll",
]


def clean_build() -> None:
    for d in [BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    spec = SPEC_FILE
    if spec.exists():
        spec.unlink()
    # Keep dist dir but clean old exe
    if DIST_DIR.exists():
        for f in DIST_DIR.glob("*.exe"):
            f.unlink()
        for f in DIST_DIR.glob("*.bin"):
            f.unlink()


def download_tools() -> None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BUILD_DIR / "imobiledevice.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # Only download if we don't have the tools yet
    if not all((TOOLS_DIR / t).exists() for t in ("irecovery.exe", "idevicerestore.exe")):
        print("[INFO] Downloading libimobiledevice Windows tools...")
        try:
            urllib.request.urlretrieve(LIBIMOBILEDEVICE_URL, zip_path)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    name = Path(member).name
                    if name in TOOLS_NEEDED:
                        with zf.open(member) as src:
                            (TOOLS_DIR / name).write_bytes(src.read())
                            print(f"  + {name}")
            print(f"[OK] Tools extracted to {TOOLS_DIR}")
        except Exception as e:
            print(f"[WARN] Could not download tools: {e}")
            print("  The .exe will work but recovery/restore tools must be installed manually.")
    else:
        print("[OK] Tools already present")


def build_exe() -> Path:
    print(f"Building {APP_NAME} v{VERSION} with PyInstaller...")

    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--add-data", f"ui{os.sep}themes{os.pathsep}ui/themes",
        "--icon", str(PROJECT_ROOT / "icon.ico") if (PROJECT_ROOT / "icon.ico").exists() else "NONE",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(PROJECT_ROOT),
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "pymobiledevice3",
        "--hidden-import", "pymobiledevice3.lockdown",
        "--hidden-import", "pymobiledevice3.exceptions",
        "--hidden-import", "pymobiledevice3.services.diagnostics",
        "--hidden-import", "pymobiledevice3.services.mobile_image_mounter",
        "--hidden-import", "usb.core",
        "--hidden-import", "usb.util",
        "--hidden-import", "config",
        "--hidden-import", "core",
        "--hidden-import", "services",
        "--hidden-import", "ui",
        "--hidden-import", "ui.widgets",
        "--hidden-import", "ui.widgets.guides",
        "--hidden-import", "utils",
        str(PROJECT_ROOT / "main.py"),
    ]

    result = subprocess.run(pyinstaller_args, capture_output=False)
    if result.returncode != 0:
        print("PyInstaller build failed!")
        sys.exit(1)

    ext = ".exe" if os.name == "nt" else ""
    exe_path = DIST_DIR / f"{APP_NAME}{ext}"
    if exe_path.exists():
        print(f"[OK] Build complete: {exe_path}")
        print(f"     Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        return exe_path
    else:
        print("[ERROR] Could not find built executable!")
        sys.exit(1)


def create_portable_bundle(exe_path: Path) -> None:
    """Copy tools next to the .exe for a portable distribution."""
    if TOOLS_DIR.exists():
        for dll in TOOLS_DIR.glob("*"):
            target = DIST_DIR / dll.name
            if not target.exists():
                shutil.copy2(dll, target)
        total = sum(f.stat().st_size for f in DIST_DIR.glob("*") if f.is_file())
        print(f"[OK] Portable bundle: {DIST_DIR}")
        print(f"     Total size: {total / 1024 / 1024:.1f} MB")
        print(f"     Files: {len(list(DIST_DIR.glob('*')))}")


def build_installer() -> None:
    iscc = shutil.which("iscc") or shutil.which("iscc.exe")
    if not iscc:
        print(
            "Inno Setup not found. Install from: https://jrsoftware.org/isdl.php\n"
            "Then add 'iscc' to your PATH."
        )
        sys.exit(1)

    installer_script = PROJECT_ROOT / "setup_installer.iss"
    if not installer_script.exists():
        print(f"Installer script not found: {installer_script}")
        sys.exit(1)

    print("Building Inno Setup installer...")
    result = subprocess.run([iscc, str(installer_script)], capture_output=False)
    if result.returncode != 0:
        print("Installer build failed!")
        sys.exit(1)
    print(f"[OK] Installer built in: {DIST_DIR}")


def main() -> None:
    build_installer_flag = "--installer" in sys.argv

    clean_build()
    download_tools()
    exe = build_exe()
    create_portable_bundle(exe)

    if build_installer_flag:
        build_installer()
        print(f"\nAll done! Files in: {DIST_DIR}")
    else:
        print(f"\nRun 'python build.py --installer' to also create an installer.")
        print(f"  Executable: {exe}")


if __name__ == "__main__":
    main()
