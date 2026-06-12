"""IPSW firmware download, verification, and management."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Callable

import config.settings as cfg

IPSW_API_BASE = "https://api.ipsw.me/v4"


class IPSWInfo:
    def __init__(self, data: dict[str, Any]) -> None:
        self.identifier: str = data.get("identifier", "")
        self.version: str = data.get("version", "")
        self.buildid: str = data.get("buildid", "")
        self.sha1sum: str = data.get("sha1sum", "")
        self.url: str = data.get("url", "")
        self.size: int = data.get("size", 0)
        self.releasedate: str = data.get("releasedate", "")

    @property
    def size_mb(self) -> str:
        return f"{self.size / (1024**3):.2f} GB"

    @property
    def filename(self) -> str:
        return self.url.split("/")[-1] if self.url else f"{self.identifier}_{self.version}.ipsw"


class IPSWService:
    def __init__(self) -> None:
        self._cache_dir = Path(cfg.PROJECT_ROOT) / ".ipsw_cache"
        self._cache_dir.mkdir(exist_ok=True)

    def fetch_firmwares(self, identifier: str) -> list[IPSWInfo]:
        url = f"{IPSW_API_BASE}/device/{identifier}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "iOSDeviceBridge/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            return []
        firmwares = data.get("firmwares", [])
        return [IPSWInfo(fw) for fw in firmwares if fw.get("signed")]

    def download_progress(
        self, ipsw: IPSWInfo, dest: str, progress_cb: Callable[[int, int], None]
    ) -> str:
        path = os.path.join(dest, ipsw.filename)
        if os.path.exists(path) and os.path.getsize(path) == ipsw.size:
            return path
        req = urllib.request.Request(ipsw.url, headers={"User-Agent": "iOSDeviceBridge/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            total = int(resp.headers.get("Content-Length", ipsw.size))
            downloaded = 0
            with open(path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress_cb(downloaded, total)
        return path

    def verify_checksum(self, path: str, expected_sha1: str) -> bool:
        sha1 = hashlib.sha1()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha1.update(chunk)
        return sha1.hexdigest().lower() == expected_sha1.lower()

    def get_restore_status(self) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["idevicerestore", "-t"],
                capture_output=True, text=True, timeout=30, check=False,
            )
            return {"status": "available" if result.returncode == 0 else "error", "output": result.stdout or result.stderr}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"status": "unavailable", "output": "idevicerestore not found"}

    def list_local_ipsw(self) -> list[dict[str, Any]]:
        ipsw_dir = Path(cfg.IPSW_DOWNLOAD_DIR)
        if not ipsw_dir.exists():
            return []
        results = []
        for f in sorted(ipsw_dir.glob("*.ipsw")):
            results.append({
                "name": f.name,
                "size": f.stat().st_size,
                "path": str(f),
                "size_gb": f"{f.stat().st_size / (1024**3):.2f} GB",
            })
        return results
