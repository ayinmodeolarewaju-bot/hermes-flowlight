"""Watched addresses. Stored outside the plugin install tree."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any


def data_dir() -> Path:
    override = os.environ.get("FLOWLIGHT_DATA_DIR", "").strip()
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path
    try:
        from plugins.plugin_storage import plugin_data_dir

        path = Path(plugin_data_dir("flowlight"))
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        path = home / "plugin-data" / "flowlight"
        path.mkdir(parents=True, exist_ok=True)
        return path


class Store:
    def __init__(self, path: Path | None = None):
        self.path = path
        self._lock = threading.Lock()
        self._memory: dict[str, Any] | None = {"watches": []} if path is None else None

    def _read(self) -> dict[str, Any]:
        if self.path is None:
            return {"watches": list((self._memory or {}).get("watches") or [])}
        if not self.path.exists():
            return {"watches": []}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"watches": []}
        if not isinstance(loaded, dict):
            return {"watches": []}
        watches = loaded.get("watches")
        if not isinstance(watches, list):
            watches = []
        return {"watches": watches}

    def _write(self, payload: dict[str, Any]) -> None:
        if self.path is None:
            self._memory = payload
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def list_watches(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._read()["watches"])

    def upsert(self, watch: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            payload = self._read()
            watches = payload["watches"]
            for index, existing in enumerate(watches):
                if existing.get("chain") == watch["chain"] and existing.get("address") == watch["address"]:
                    merged = dict(existing)
                    merged.update(watch)
                    watches[index] = merged
                    self._write(payload)
                    return merged
            watches.append(watch)
            self._write(payload)
            return watch

    def remove(self, chain: str, address: str) -> bool:
        with self._lock:
            payload = self._read()
            kept = [
                item
                for item in payload["watches"]
                if not (item.get("chain") == chain and item.get("address") == address)
            ]
            removed = len(kept) != len(payload["watches"])
            payload["watches"] = kept
            if removed:
                self._write(payload)
            return removed
