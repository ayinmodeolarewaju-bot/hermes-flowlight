"""JSON handlers shared by the dashboard routes and the loopback page."""

from __future__ import annotations

from typing import Any

from .runtime import Deps, make_deps
from .service import flow_list, list_accounts, summary_only, unwatch_accounts, watch_accounts, graph

_SHARED: Deps | None = None


def shared_deps() -> Deps:
    global _SHARED
    if _SHARED is None:
        _SHARED = make_deps()
    return _SHARED


def reset_shared_deps(deps: Deps | None = None) -> None:
    global _SHARED
    _SHARED = deps


def _flag(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def view_graph(query: dict[str, Any] | None = None, deps: Deps | None = None) -> dict[str, Any]:
    query = query or {}
    window = query.get("window_hours") or query.get("window") or 0
    try:
        hours = int(window)
    except (TypeError, ValueError):
        hours = 0
    return graph(
        deps or shared_deps(),
        demo=_flag(query.get("demo")),
        live=_flag(query.get("live")),
        window_hours=hours or None,
    )


def view_summary(query: dict[str, Any] | None = None, deps: Deps | None = None) -> dict[str, Any]:
    query = query or {}
    return summary_only(
        {
            "demo": _flag(query.get("demo")),
            "live": _flag(query.get("live")),
            "window_hours": query.get("window_hours") or None,
        },
        deps or shared_deps(),
    )


def view_flows(query: dict[str, Any] | None = None, deps: Deps | None = None) -> dict[str, Any]:
    query = query or {}
    return flow_list(
        {
            "demo": _flag(query.get("demo")),
            "live": _flag(query.get("live")),
            "window_hours": query.get("window_hours") or None,
            "limit": query.get("limit") or 40,
            "chain": query.get("chain") or "",
            "address": query.get("address") or "",
        },
        deps or shared_deps(),
    )


def view_watches(deps: Deps | None = None) -> dict[str, Any]:
    return list_accounts(deps or shared_deps())


def post_watch(body: dict[str, Any], deps: Deps | None = None) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"ok": False, "error": "JSON object required", "read_only": True, "funds_moved": False}
    return watch_accounts(body, deps or shared_deps())


def post_unwatch(body: dict[str, Any], deps: Deps | None = None) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"ok": False, "error": "JSON object required", "read_only": True, "funds_moved": False}
    return unwatch_accounts(body, deps or shared_deps())
