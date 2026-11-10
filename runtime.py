"""Host settings and the objects tools share."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .httpclient import HttpClient
from .store import Store, data_dir


@dataclass
class Settings:
    lookback_hours: int = 24
    max_flows: int = 180
    cache_ttl_seconds: int = 45
    demo_mode: bool = False
    budget_seconds: float = 14


@dataclass
class Deps:
    http: HttpClient
    store: Store
    settings: Settings
    now: Any = None
    fetcher: Any = None
    ledger_path: Path | None = None


def _config_value(ctx: Any, key: str, default: Any) -> Any:
    if ctx is None or not hasattr(ctx, "get_config"):
        return default
    try:
        value = ctx.get_config(key, default=default)
    except TypeError:
        try:
            value = ctx.get_config(key)
        except Exception:
            return default
    except Exception:
        return default
    if value is None or value == "":
        return default
    return value


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def settings_from_host(ctx: Any = None) -> Settings:
    settings = Settings()
    if os.environ.get("FLOWLIGHT_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}:
        settings.demo_mode = True
    settings.lookback_hours = int(_config_value(ctx, "lookback_hours", settings.lookback_hours) or settings.lookback_hours)
    settings.max_flows = int(_config_value(ctx, "max_flows", settings.max_flows) or settings.max_flows)
    settings.cache_ttl_seconds = int(_config_value(ctx, "cache_ttl_seconds", settings.cache_ttl_seconds) or settings.cache_ttl_seconds)
    settings.demo_mode = _as_bool(_config_value(ctx, "demo_mode", settings.demo_mode), settings.demo_mode)
    if ctx is None:
        try:
            from hermes_cli.config import load_config_readonly

            loaded = load_config_readonly() or {}
            entry = ((loaded.get("plugins") or {}).get("entries") or {}).get("flowlight") or {}
            block = entry.get("settings") or {}
            if isinstance(block, dict):
                if block.get("lookback_hours") not in (None, ""):
                    settings.lookback_hours = int(block["lookback_hours"])
                if block.get("max_flows") not in (None, ""):
                    settings.max_flows = int(block["max_flows"])
                if block.get("cache_ttl_seconds") not in (None, ""):
                    settings.cache_ttl_seconds = int(block["cache_ttl_seconds"])
                if "demo_mode" in block:
                    settings.demo_mode = _as_bool(block.get("demo_mode"), settings.demo_mode)
        except Exception:
            pass
    settings.lookback_hours = max(1, min(settings.lookback_hours, 168))
    settings.max_flows = max(10, min(settings.max_flows, 400))
    settings.cache_ttl_seconds = max(5, min(settings.cache_ttl_seconds, 600))
    return settings


def make_deps(ctx: Any = None, **overrides: Any) -> Deps:
    settings = overrides.get("settings") or settings_from_host(ctx)
    store = overrides.get("store")
    if store is None:
        path = overrides.get("store_path")
        if path is None:
            path = data_dir() / "watches.json"
        store = Store(Path(path))
    http = overrides.get("http") or HttpClient()
    return Deps(
        http=http,
        store=store,
        settings=settings,
        now=overrides.get("now"),
        fetcher=overrides.get("fetcher"),
    )
