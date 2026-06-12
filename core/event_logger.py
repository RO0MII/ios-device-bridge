"""Device connection history and event logging."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import config.settings as cfg
from core.mode_detector import DeviceMode


class EventLogger:
    def __init__(self) -> None:
        self._path = Path(cfg.PROJECT_ROOT) / "device_history.json"
        self._events: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._events = data if isinstance(data, list) else []
            except Exception:
                self._events = []

    def _save(self) -> None:
        try:
            recent = self._events[-500:]
            self._path.write_text(json.dumps(recent, indent=2), encoding="utf-8")
        except Exception:
            pass

    def log(
        self,
        event: str,
        mode: str = "",
        model: str = "",
        udid: str = "",
        ios_version: str = "",
    ) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "mode": mode,
            "model": model,
            "udid": udid[:8] + "..." if udid else "",
            "ios_version": ios_version,
        }
        self._events.append(entry)
        self._save()

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._events[-limit:]

    def log_connection(self, mode: DeviceMode, model: str = "", udid: str = "", ios: str = "") -> None:
        if mode == DeviceMode.DISCONNECTED:
            self.log("Device disconnected", mode=mode.label)
        else:
            self.log("Device connected", mode=mode.label, model=model, udid=udid, ios_version=ios)

    def log_error(self, message: str) -> None:
        self.log(f"Error: {message}")

    def log_action(self, action: str, details: str = "") -> None:
        text = action + (f" ({details})" if details else "")
        self.log(text)

    def clear(self) -> None:
        self._events.clear()
        self._save()
