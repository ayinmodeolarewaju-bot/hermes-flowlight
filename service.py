"""Watch list, live reads, and the graph payload the picture draws."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .chains import explorer_address, known_label, node_id, normalize_address
from .demo_data import build_demo
from . import invoices as invoice_book
from .money import short_address
from .narrate import summarize
from .parse import InputError, coerce_watch_args, secret_material_error
from .providers import fetch_prices, fetch_watch
from .runtime import Deps

_SAFETY = {"read_only": True, "funds_moved": False, "signing": False}


def _now(deps: Deps) -> float:
    if deps.now is not None:
        return float(deps.now())
    return time.time()


def _base(ok: bool = True, **extra: Any) -> dict[str, Any]:
    payload = {"ok": ok, **_SAFETY}
    payload.update(extra)
    return payload


def _fail(message: str, code: str = "bad_request") -> dict[str, Any]:
    return _base(False, error=message, code=code, summary={"text": message})


def _annotate(flows: list[dict[str, Any]], watches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    watched = {(item["chain"], item["address"]) for item in watches}
    annotated = []
    for flow in flows:
        row = dict(flow)
        src = (row["chain"], row["src"])
        dst = (row["chain"], row["dst"])
        if src in watched and dst in watched:
            row["direction"] = "internal"
        elif dst in watched:
            row["direction"] = "in"
        elif src in watched:
            row["direction"] = "out"
        else:
            row["direction"] = "related"
        annotated.append(row)
    return annotated


def _nodes(flows: list[dict[str, Any]], watches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for watch in watches:
        ident = node_id(watch["chain"], watch["address"])
        nodes[ident] = {
            "id": ident,
            "chain": watch["chain"],
            "address": watch["address"],
            "label": watch.get("label") or known_label(watch["chain"], watch["address"]) or short_address(watch["address"]),
            "watched": True,
            "kind": "account",
            "explorer": explorer_address(watch["chain"], watch["address"]),
        }
    for flow in flows:
        for side in ("src", "dst"):
            address = flow[side]
            ident = node_id(flow["chain"], address)
            label = flow.get(f"{side}_label") or known_label(flow["chain"], address) or short_address(address)
            current = nodes.get(ident)
            if current is None:
                nodes[ident] = {
                    "id": ident,
                    "chain": flow["chain"],
                    "address": address,
                    "label": label,
                    "watched": False,
                    "kind": "contract" if label in {"USDC", "USDT", "WETH", "wNEAR", "AERO"} else "account",
                    "explorer": explorer_address(flow["chain"], address),
                }
            elif current["label"] == short_address(address) and label and label != short_address(address):
                current["label"] = label
    return list(nodes.values())


def _select(flows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(flows) <= limit:
        return flows
    by_value = sorted(
        flows,
        key=lambda row: float(row["usd"]) if row.get("usd") is not None else float(row.get("amount_value") or 0),
        reverse=True,
    )
    by_time = sorted(flows, key=lambda row: int(row.get("ts") or 0), reverse=True)
    chosen: dict[str, dict[str, Any]] = {}
    for row in by_value[: int(limit * 0.7)] + by_time[: limit]:
        chosen[str(row["id"])] = row
        if len(chosen) >= limit:
            break
    return sorted(chosen.values(), key=lambda row: int(row.get("ts") or 0), reverse=True)


def _cache_file(deps: Deps):
    if deps.store.path is None:
        return None
    return deps.store.path.parent / "flow-cache.json"


def _cache_key(watches: list[dict[str, Any]], deps: Deps) -> str:
    pairs = sorted((item["chain"], item["address"]) for item in watches)
    return json.dumps({"watches": pairs, "hours": deps.settings.lookback_hours, "max": deps.settings.max_flows})


def _read_cache(deps: Deps, watches: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]] | None:
    path = _cache_file(deps)
    if path is None or not path.exists():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if blob.get("key") != _cache_key(watches, deps):
        return None
    age = time.time() - float(blob.get("at") or 0)
    if age > deps.settings.cache_ttl_seconds:
        return None
    flows = blob.get("flows")
    warnings = blob.get("warnings")
    if not isinstance(flows, list) or not isinstance(warnings, list):
        return None
    return flows, [str(item) for item in warnings]


def _write_cache(deps: Deps, watches: list[dict[str, Any]], flows: list[dict[str, Any]], warnings: list[str]) -> None:
    path = _cache_file(deps)
    if path is None:
        return
    payload = {"key": _cache_key(watches, deps), "at": time.time(), "flows": flows, "warnings": warnings}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(path)
    except OSError:
        return


def collect(deps: Deps, watches: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    if deps.fetcher is not None:
        flows, warnings = deps.fetcher(watches, deps)
        return _annotate(flows, watches), list(warnings)
    if not watches:
        return [], []
    cached = _read_cache(deps, watches)
    if cached is not None:
        return cached
    prices = fetch_prices(deps.http, {"ETH", "NEAR", "SOL", "BTC", "USDC", "USDT", "DAI"})
    deadline = time.monotonic() + deps.settings.budget_seconds
    warnings: list[str] = []
    found: list[dict[str, Any]] = []

    def _one(watch: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            return fetch_watch(
                watch,
                deps.http,
                prices,
                deadline=deadline,
                lookback_hours=deps.settings.lookback_hours,
                cap=max(40, deps.settings.max_flows // max(1, len(watches))),
            )
        except Exception as exc:  # noqa: BLE001 — one chain must not blank the rest
            return [], [f"{watch.get('chain')}: {exc}"]

    workers = min(4, len(watches))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one, watch) for watch in watches]
        for future in as_completed(futures):
            rows, notes = future.result()
            found.extend(rows)
            warnings.extend(notes)
    chosen = _select(_annotate(found, watches), deps.settings.max_flows)
    _write_cache(deps, watches, chosen, warnings)
    return chosen, warnings


def _public_flow(flow: dict[str, Any]) -> dict[str, Any]:
    shown = dict(flow)
    shown.pop("amount_value", None)
    return shown


def _apply_phase(payload: dict[str, Any], phase: str | None) -> dict[str, Any]:
    if phase not in {"pending", "paid"}:
        return payload
    rows = list(payload.get("invoices") or [])
    if phase == "pending":
        payload["invoices"] = [item for item in rows if item.get("pending")]
        payload["invoice_arcs"] = []
    else:
        payload["invoices"] = [item for item in rows if item.get("paid")]
    return payload


def _mention(summary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    line = invoice_book.sentence(rows)
    if not line:
        return summary
    updated = dict(summary)
    updated["text"] = (str(summary.get("text") or "").rstrip() + " " + line).strip()
    updated["invoice_pending"] = sum(1 for item in rows if item.get("pending"))
    updated["invoice_paid"] = sum(1 for item in rows if item.get("paid"))
    return updated


def graph(
    deps: Deps,
    *,
    demo: bool = False,
    live: bool = False,
    window_hours: int | None = None,
    phase: str | None = None,
) -> dict[str, Any]:
    use_demo = (deps.settings.demo_mode or demo) and not live
    if use_demo:
        payload = build_demo(_now(deps))
        payload["generated_at"] = int(_now(deps))
        return _apply_phase(payload, phase)
    prepared, note, ledger_state, extra_warnings = invoice_book.prepare(deps)
    added = invoice_book.autowatch(deps, prepared)
    watches = deps.store.list_watches()
    if window_hours:
        deps.settings.lookback_hours = max(1, min(int(window_hours), 168))
    flows, warnings = collect(deps, watches)
    warnings = list(warnings) + extra_warnings
    bound = invoice_book.match_flows(prepared, flows)
    public = [invoice_book.public_invoice(item) for item in bound]
    summary = _mention(
        summarize(flows, watches, requested_hours=deps.settings.lookback_hours, warnings=warnings),
        public,
    )
    return _base(
        demo=False,
        mode="live",
        generated_at=int(_now(deps)),
        warnings=warnings,
        watches=watches,
        flows=[_public_flow(flow) for flow in flows],
        nodes=_nodes(flows, watches),
        summary=summary,
        invoices=public,
        invoice_arcs=invoice_book.invoice_arcs(bound),
        invoice_note=note if not public else "",
        invoice_watches=added,
        ledger=ledger_state,
    )


def watch_accounts(args: dict[str, Any], deps: Deps) -> dict[str, Any]:
    try:
        targets = coerce_watch_args(args or {})
    except InputError as exc:
        return _fail(str(exc))
    label = str((args or {}).get("label") or "").strip()
    saved = []
    now = int(_now(deps))
    for target in targets:
        item = {
            "chain": target["chain"],
            "address": normalize_address(target["chain"], target["address"]),
            "label": label or known_label(target["chain"], target["address"]) or "",
            "added_at": now,
        }
        if not item["label"]:
            item["label"] = short_address(item["address"])
        saved.append(deps.store.upsert(item))
    if (args or {}).get("demo") is True and not saved:
        return graph(deps, demo=True)
    picture = graph(deps, demo=bool((args or {}).get("demo")))
    picture["added"] = saved
    picture["summary"] = dict(picture.get("summary") or {})
    names = ", ".join(f"{item['address']} on {item['chain']}" for item in saved)
    picture["summary"]["text"] = f"Watching {names}. " + str(picture["summary"].get("text") or "")
    return picture


def unwatch_accounts(args: dict[str, Any], deps: Deps) -> dict[str, Any]:
    secret = secret_material_error(str((args or {}).get("address") or "")) or secret_material_error(str((args or {}).get("text") or ""))
    if secret:
        return _fail(secret)
    try:
        targets = coerce_watch_args(args or {})
    except InputError as exc:
        return _fail(str(exc))
    removed = []
    missing = []
    for target in targets:
        address = normalize_address(target["chain"], target["address"])
        if deps.store.remove(target["chain"], address):
            removed.append({"chain": target["chain"], "address": address})
        else:
            missing.append({"chain": target["chain"], "address": address})
    watches = deps.store.list_watches()
    text = "Stopped watching " + ", ".join(f"{item['address']} on {item['chain']}" for item in removed) if removed else "Nothing matched that watch."
    if missing:
        text += " Not in the list: " + ", ".join(f"{item['address']} on {item['chain']}" for item in missing) + "."
    return _base(removed=removed, missing=missing, watches=watches, summary={"text": text})


def list_accounts(deps: Deps) -> dict[str, Any]:
    watches = deps.store.list_watches()
    if not watches:
        text = "Flowlight is not watching any address. Example: watch purefile1686.near and 0x… on Base."
    else:
        text = "Watching " + ", ".join(f"{item.get('label') or item['address']} on {item['chain']}" for item in watches) + "."
    return _base(watches=watches, count=len(watches), summary={"text": text})


def flow_list(args: dict[str, Any], deps: Deps) -> dict[str, Any]:
    demo = bool((args or {}).get("demo"))
    live = bool((args or {}).get("live"))
    window = (args or {}).get("window_hours")
    picture = graph(deps, demo=demo, live=live, window_hours=int(window) if window else None)
    chain = str((args or {}).get("chain") or "").strip().lower()
    address = str((args or {}).get("address") or "").strip()
    flows = picture.get("flows") or []
    if chain:
        flows = [flow for flow in flows if flow.get("chain") == chain]
    if address:
        flows = [flow for flow in flows if address.lower() in {str(flow.get("src", "")).lower(), str(flow.get("dst", "")).lower()}]
    limit = int((args or {}).get("limit") or 40)
    flows = flows[: max(1, min(limit, 200))]
    picture = dict(picture)
    picture["flows"] = flows
    picture["count"] = len(flows)
    return picture


def summary_only(args: dict[str, Any], deps: Deps) -> dict[str, Any]:
    picture = flow_list(args or {}, deps)
    return _base(
        demo=picture.get("demo", False),
        mode=picture.get("mode", "live"),
        warnings=picture.get("warnings") or [],
        watches=picture.get("watches") or [],
        summary=picture.get("summary") or {"text": ""},
        invoices=picture.get("invoices") or [],
        count=(picture.get("summary") or {}).get("count", 0),
    )


def invoice_report(args: dict[str, Any], deps: Deps) -> dict[str, Any]:
    demo = bool((args or {}).get("demo"))
    live = bool((args or {}).get("live"))
    phase = str((args or {}).get("phase") or "") or None
    picture = graph(deps, demo=demo, live=live, phase=phase if demo else None)
    rows = picture.get("invoices") or []
    note = picture.get("invoice_note") or ("" if rows else invoice_book.QUIET)
    text = (picture.get("summary") or {}).get("text") if rows else note
    return _base(
        demo=picture.get("demo", False),
        mode=picture.get("mode", "live"),
        invoices=rows,
        invoice_arcs=picture.get("invoice_arcs") or [],
        note=note,
        ledger=picture.get("ledger"),
        warnings=picture.get("warnings") or [],
        watches=picture.get("watches") or [],
        summary={"text": text or note},
    )
