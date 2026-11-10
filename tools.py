"""Tool handlers. Each returns a JSON string and never raises."""

from __future__ import annotations

import json
from typing import Any

from .runtime import make_deps
from .service import flow_list, list_accounts, summary_only, unwatch_accounts, watch_accounts

_BOUND_CTX: Any = None


def bind_context(ctx: Any) -> None:
    global _BOUND_CTX
    _BOUND_CTX = ctx


def _deps(kwargs: dict[str, Any]):
    override = kwargs.get("_deps")
    if override is not None:
        return override
    return make_deps(_BOUND_CTX)


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


def flowlight_watch(args: dict[str, Any], **kwargs: Any) -> str:
    try:
        return _dump(watch_accounts(args or {}, _deps(kwargs)))
    except Exception as exc:  # noqa: BLE001
        return _dump({"ok": False, "error": f"flowlight_watch failed: {exc}", "funds_moved": False, "read_only": True})


def flowlight_unwatch(args: dict[str, Any], **kwargs: Any) -> str:
    try:
        return _dump(unwatch_accounts(args or {}, _deps(kwargs)))
    except Exception as exc:  # noqa: BLE001
        return _dump({"ok": False, "error": f"flowlight_unwatch failed: {exc}", "funds_moved": False, "read_only": True})


def flowlight_flows(args: dict[str, Any], **kwargs: Any) -> str:
    try:
        return _dump(flow_list(args or {}, _deps(kwargs)))
    except Exception as exc:  # noqa: BLE001
        return _dump({"ok": False, "error": f"flowlight_flows failed: {exc}", "funds_moved": False, "read_only": True})


def flowlight_summary(args: dict[str, Any], **kwargs: Any) -> str:
    try:
        return _dump(summary_only(args or {}, _deps(kwargs)))
    except Exception as exc:  # noqa: BLE001
        return _dump({"ok": False, "error": f"flowlight_summary failed: {exc}", "funds_moved": False, "read_only": True})


def flowlight_list(args: dict[str, Any], **kwargs: Any) -> str:
    try:
        return _dump(list_accounts(_deps(kwargs)))
    except Exception as exc:  # noqa: BLE001
        return _dump({"ok": False, "error": f"flowlight_list failed: {exc}", "funds_moved": False, "read_only": True})


HANDLERS = {
    "flowlight_watch": flowlight_watch,
    "flowlight_unwatch": flowlight_unwatch,
    "flowlight_flows": flowlight_flows,
    "flowlight_summary": flowlight_summary,
    "flowlight_list": flowlight_list,
}
