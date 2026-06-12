"""Recovery and DFU mode interaction via irecovery/libimobiledevice."""

from __future__ import annotations

import shutil
import subprocess

from core.exceptions import RecoveryCommandError


class RecoveryService:

    def __init__(self) -> None:
        from pathlib import Path
        self._tools_dir = str(Path(__file__).resolve().parent.parent / "dist" / "tools")
        self._irecovery = self._find_tool("irecovery")

    def _find_tool(self, name: str):
        found = shutil.which(name) or shutil.which(name + ".exe")
        if not found:
            bundled = Path(self._tools_dir) / (name + ".exe")
            if bundled.exists():
                found = str(bundled)
        return found or None

    def exit_recovery(self) -> None:
        """Send reboot command to exit Recovery Mode."""
        self._run_irecovery(["-n"], "Failed to exit Recovery Mode.")

    def enter_recovery(self) -> None:
        """Enter Recovery Mode using multiple methods (tries each in order)."""
        methods = [
            ("pymobiledevice3", self._enter_recovery_pymobile),
            ("ideviceenterrecovery", self._enter_recovery_idevice),
        ]
        errors = []
        for name, method in methods:
            try:
                method()
                return
            except (RecoveryCommandError, ImportError, FileNotFoundError) as exc:
                errors.append(f"  {name}: {exc}")
        raise RecoveryCommandError(
            "Could not enter Recovery Mode. None of the available methods succeeded.\n"
            f"Tried:\n" + "\n".join(errors) + "\n\n"
            "Manual method: Press and hold Power + Volume Down to enter Recovery Mode."
        )

    def _enter_recovery_pymobile(self) -> None:
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            lockdown = create_using_usbmux()
            lockdown.enter_recovery()
        except ImportError as exc:
            raise RecoveryCommandError(str(exc)) from exc
        except Exception as exc:
            raise RecoveryCommandError(f"pymobiledevice3: {exc}") from exc

    def _enter_recovery_idevice(self) -> None:
        tool = self._find_tool("ideviceenterrecovery")
        if not tool:
            raise FileNotFoundError(
                "ideviceenterrecovery not found. Install libimobiledevice tools."
            )
        try:
            result = subprocess.run(
                [tool],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                raise RecoveryCommandError(
                    f"ideviceenterrecovery failed:\n{result.stderr or result.stdout}"
                )
        except subprocess.TimeoutExpired as exc:
            raise RecoveryCommandError("ideviceenterrecovery timed out.") from exc

    def get_recovery_info(self) -> dict[str, str]:
        """Read ECID and mode info when in recovery/DFU."""
        if not self._irecovery:
            return {"irecovery": "Not installed"}
        try:
            result = subprocess.run(
                [self._irecovery, "-q"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            info: dict[str, str] = {}
            for line in result.stdout.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    info[key.strip()] = value.strip()
            return info
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            raise RecoveryCommandError(str(exc)) from exc

    def restore(self, ipsw_path: str) -> subprocess.Popen:
        """Start iPhone restore using idevicerestore with the given IPSW path."""
        idevicerestore = self._find_tool("idevicerestore")
        if not idevicerestore:
            raise RecoveryCommandError(
                "idevicerestore not found. Install libimobiledevice tools for Windows."
            )
        return subprocess.Popen(
            [idevicerestore, "-y", ipsw_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def reboot(self) -> None:
        """Reboot device in recovery mode."""
        self._run_irecovery(["-n"], "Failed to reboot device.")

    def get_ecid(self) -> str:
        """Get device ECID from recovery mode."""
        info = self.get_recovery_info()
        return info.get("ECID", "Unknown")

    def _run_irecovery(self, args: list[str], error_message: str) -> None:
        if not self._irecovery:
            raise RecoveryCommandError(
                "irecovery not found. Install libimobiledevice tools for Windows."
            )
        try:
            result = subprocess.run(
                [self._irecovery, *args],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                raise RecoveryCommandError(
                    f"{error_message}\n{result.stderr or result.stdout}"
                )
        except subprocess.TimeoutExpired as exc:
            raise RecoveryCommandError("irecovery command timed out.") from exc
