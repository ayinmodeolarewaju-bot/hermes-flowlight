"""Dashboard routes mounted at /api/plugins/flowlight/.

Loaded by file path, so the plugin package is imported explicitly. The routes
are the same read-only handlers the loopback page uses.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()
_ROOT = Path(__file__).resolve().parents[1]


def _webapi():
    for name, module in list(sys.modules.items()):
        if getattr(module, "PLUGIN_ID", None) == "flowlight":
            web = sys.modules.get(name + ".webapi")
            if web is not None:
                return web
    package = "flowlight_plugin"
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            package,
            _ROOT / "__init__.py",
            submodule_search_locations=[str(_ROOT)],
        )
        module = importlib.util.module_from_spec(spec)
        module.__package__ = package
        module.__path__ = [str(_ROOT)]
        sys.modules[package] = module
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
    return importlib.import_module(package + ".webapi")


@router.get("/health")
def health() -> dict:
    return {"ok": True, "plugin": "flowlight", "read_only": True, "funds_moved": False}


@router.get("/graph")
def graph(demo: int = 0, live: int = 0, window_hours: int = 0, phase: str = "") -> dict:
    return _webapi().view_graph({"demo": demo, "live": live, "window_hours": window_hours, "phase": phase})


@router.get("/summary")
def summary(demo: int = 0, live: int = 0, window_hours: int = 0) -> dict:
    return _webapi().view_summary({"demo": demo, "live": live, "window_hours": window_hours})


@router.get("/flows")
def flows(demo: int = 0, live: int = 0, window_hours: int = 0, limit: int = 40) -> dict:
    return _webapi().view_flows({"demo": demo, "live": live, "window_hours": window_hours, "limit": limit})


@router.get("/watches")
def watches() -> dict:
    return _webapi().view_watches()


@router.get("/invoices")
def invoices(demo: int = 0, live: int = 0, phase: str = "") -> dict:
    return _webapi().view_invoices({"demo": demo, "live": live, "phase": phase})


@router.post("/watch")
def watch(body: dict) -> dict:
    return _webapi().post_watch(body if isinstance(body, dict) else {})


@router.post("/unwatch")
def unwatch(body: dict) -> dict:
    return _webapi().post_unwatch(body if isinstance(body, dict) else {})
