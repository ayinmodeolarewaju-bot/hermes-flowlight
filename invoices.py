"""Read-only view of an Intents Pay invoice ledger.

Flowlight does not import Intents Pay. It reads the JSON ledger that plugin
writes under the profile plugin-data directory, and it may GET
``https://1click.chaindefuser.com/v0/status`` for a deposit address. It never
creates a quote, never writes the ledger, and never handles a key.

Missing, empty, and unreadable ledgers all report ``no Intents Pay invoices found``.
"""

from __future__ import annotations

import json
import os
import time
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .chains import (
    EVM_CHAINS,
    canonical_chain,
    explorer_address,
    is_evm_address,
    is_near_account,
    is_solana_address,
    node_id,
    normalize_address,
)
from .httpclient import USER_AGENT, HttpError
from .money import format_amount, short_address, to_decimal
from .runtime import Deps

ONECLICK_STATUS = "https://1click.chaindefuser.com/v0/status"
QUIET = "no Intents Pay invoices found"
_PAID = {"SUCCESS"}
_CLOSED = {"REFUNDED", "FAILED"}
_STATUS_LABELS = {
    "DRY_QUOTE": "Dry quote only. There is no deposit to track.",
    "PENDING_DEPOSIT": "Waiting for the payer to send funds",
    "KNOWN_DEPOSIT_TX": "Deposit transaction seen",
    "INCOMPLETE_DEPOSIT": "Deposit is short of the quoted amount",
    "PROCESSING": "Swap in progress",
    "SUCCESS": "Payment settled",
    "REFUNDED": "Funds were refunded to the refund address",
    "FAILED": "Swap failed",
}
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 45.0
_HIDDEN = {"raw_quote", "signature", "confirmation_token", "api_key", "private_key", "seed"}


def locate_ledger(explicit: Path | None = None) -> Path | None:
    """Path of the Intents Pay ledger. Does not create directories."""
    if explicit is not None:
        return explicit
    override = os.environ.get("FLOWLIGHT_INTENTS_LEDGER", "").strip()
    if override:
        return Path(override)
    home = _hermes_home()
    if home is None:
        return None
    return home / "plugin-data" / "intents-pay" / "ledger.json"


def _hermes_home() -> Path | None:
    try:
        from hermes_constants import get_hermes_home

        return Path(get_hermes_home())
    except Exception:
        raw = os.environ.get("HERMES_HOME", "").strip()
        if raw:
            return Path(raw)
        return Path.home() / ".hermes"


def read_ledger(path: Path | None) -> tuple[list[dict[str, Any]], str, str]:
    """Return ``(rows, note, state)``.

    ``state`` is ``missing``, ``malformed``, ``empty``, or ``ok``.
    The note is the quiet sentence whenever there is nothing to draw.
    """
    if path is None or not path.is_file():
        return [], QUIET, "missing"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], QUIET, "malformed"
    if not isinstance(loaded, dict):
        return [], QUIET, "malformed"
    rows = loaded.get("invoices")
    if not isinstance(rows, list):
        return [], QUIET, "malformed"
    clean = [row for row in rows if isinstance(row, dict)]
    if not clean:
        return [], QUIET, "empty"
    return clean, "", "ok"


def status_url(deposit_address: str, deposit_memo: str | None = None) -> str:
    query = {"depositAddress": deposit_address}
    if deposit_memo:
        query["depositMemo"] = deposit_memo
    return ONECLICK_STATUS + "?" + urlencode(query)


def fetch_click_status(deps: Deps, deposit_address: str, deposit_memo: str | None) -> dict[str, Any] | None:
    """One GET /v0/status. Failures return None so the ledger status still stands."""
    if not deposit_address or deps.http is None:
        return None
    url = status_url(deposit_address, deposit_memo)
    now = time.monotonic()
    cached = _CACHE.get(url)
    if cached and now - cached[0] < _CACHE_TTL:
        return dict(cached[1])
    try:
        payload = deps.http.get_json_once(url, timeout=4)
    except (HttpError, OSError, ValueError, TimeoutError):
        return None
    if not isinstance(payload, dict):
        return None
    _CACHE[url] = (now, payload)
    return payload


def clear_status_cache() -> None:
    _CACHE.clear()


def _status_label(status: str) -> str:
    if not status:
        return "Unknown"
    return _STATUS_LABELS.get(status, status.replace("_", " ").title())


def _chain_for(address: str, hint: str | None) -> str | None:
    hinted = canonical_chain(hint) if hint else None
    if is_near_account(address):
        return "near"
    if is_evm_address(address):
        if hinted in EVM_CHAINS:
            return hinted
        return None
    if hinted == "solana" and is_solana_address(address):
        return "solana"
    return None


def _norm(chain: str | None, address: str) -> str:
    if not chain:
        return (address or "").strip()
    return normalize_address(chain, address)


def _tokens_match(invoice_token: str, flow_token: str) -> bool:
    left = (invoice_token or "").upper()
    right = (flow_token or "").upper()
    if not left or not right:
        return False
    if left == right:
        return True
    if left == "NEAR" and right in {"NEAR", "WNEAR"}:
        return True
    if left in {"USDT", "USDT0"} and right in {"USDT", "USDT0"}:
        return True
    return False


def _amounts_close(expected: Decimal, actual: Decimal) -> bool:
    if expected <= 0 or actual <= 0:
        return False
    tolerance = max(Decimal("0.02"), abs(expected) * Decimal("0.01"))
    return abs(expected - actual) <= tolerance


def _amount_text(record: dict[str, Any]) -> str:
    raw = record.get("amount")
    if raw in (None, ""):
        raw = record.get("amount_out_formatted")
    amount = to_decimal(raw)
    if amount == 0 and raw not in (None, "", 0, "0"):
        return str(raw)
    return format_amount(amount)


def _expected_amounts(record: dict[str, Any]) -> list[Decimal]:
    found: list[Decimal] = []
    for key in ("amount", "amount_out_formatted"):
        value = to_decimal(record.get(key))
        if value > 0 and value not in found:
            found.append(value)
    return found


def prepare(deps: Deps) -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Parse the ledger and refresh non-final deposit statuses. No chain flows yet."""
    path = locate_ledger(deps.ledger_path)
    rows, note, state = read_ledger(path)
    warnings: list[str] = []
    if state == "malformed":
        warnings.append("Intents Pay ledger could not be read.")
    prepared: list[dict[str, Any]] = []
    for record in rows:
        public = _public_base(record)
        if public is None:
            continue
        ledger_status = str(record.get("payment_status") or "").strip().upper()
        source = "ledger"
        updated = record.get("status_updated_at") or record.get("updated_at")
        deposit = public.get("deposit_address") or ""
        if deposit and ledger_status not in _PAID | _CLOSED:
            live = fetch_click_status(deps, deposit, record.get("deposit_memo") or None)
            live_status = str((live or {}).get("status") or "").strip().upper()
            if live_status:
                ledger_status = live_status
                source = "1click"
                updated = (live or {}).get("updatedAt") or updated
        public["status"] = ledger_status or "UNKNOWN"
        public["status_label"] = _status_label(public["status"])
        public["status_source"] = source
        public["updated_at"] = updated
        public["paid"] = public["status"] in _PAID
        public["pending"] = not public["paid"] and public["status"] not in _CLOSED
        prepared.append(public)
    if not prepared and not note:
        note = QUIET
    return prepared, note, state, warnings


def autowatch(deps: Deps, invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remember each invoice recipient and, when the chain is known, its deposit address."""
    if deps.store is None or not invoices:
        return []
    existing = {(item.get("chain"), item.get("address")) for item in deps.store.list_watches()}
    added: list[dict[str, Any]] = []
    now = int(time.time())
    for invoice in invoices:
        targets = [
            (invoice.get("recipient_chain"), invoice.get("recipient"), invoice.get("recipient")),
            (invoice.get("deposit_chain"), invoice.get("deposit_address"), None),
        ]
        for chain, address, label in targets:
            if not chain or not address:
                continue
            key = (chain, address)
            if key in existing:
                continue
            item = {
                "chain": chain,
                "address": address,
                "label": label or short_address(address),
                "added_at": now,
                "source": "intents-pay",
            }
            saved = deps.store.upsert(item)
            existing.add(key)
            added.append(saved)
    return added


def match_flows(invoices: list[dict[str, Any]], flows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark an invoice paid when an inflow of the same token and amount reaches the recipient."""
    matched: list[dict[str, Any]] = []
    for invoice in invoices:
        row = dict(invoice)
        hit = _matching_flow(row, flows)
        if hit is not None and row["status"] not in _CLOSED:
            row["matched_flow_id"] = hit.get("id")
            row["explorer"] = hit.get("explorer") or row.get("explorer")
            row["paid_at"] = row.get("paid_at") or _iso(hit.get("ts"))
            if not row["paid"]:
                row["paid"] = True
                row["pending"] = False
                row["status_source"] = "on-chain"
                if row["status"] not in _PAID:
                    row["status"] = "SUCCESS"
                    row["status_label"] = _status_label("SUCCESS")
        if row["paid"]:
            number = row.get("number") or row.get("id")
            row["badge"] = f"invoice {number} paid · {row['amount']} {row['token']}"
        else:
            row["badge"] = ""
        matched.append(row)
    return matched


def invoice_arcs(invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    arcs = []
    for invoice in invoices:
        if not invoice.get("paid"):
            continue
        recipient_id = invoice.get("recipient_id")
        if not recipient_id:
            continue
        origin_id = invoice.get("deposit_id") or invoice.get("matched_from_id")
        origin_chain = invoice.get("deposit_chain") or invoice.get("matched_from_chain")
        origin_address = invoice.get("deposit_address") or invoice.get("matched_from")
        origin_label = invoice.get("matched_from_label") or (short_address(origin_address) if origin_address else "")
        if not origin_id:
            origin_id = ""
        arcs.append(
            {
                "id": "invoice:" + str(invoice.get("id") or invoice.get("number")),
                "invoice_id": invoice.get("id"),
                "number": invoice.get("number"),
                "from_id": origin_id,
                "to_id": recipient_id,
                "from_chain": origin_chain or "",
                "from_address": origin_address or "",
                "from_label": origin_label or "Intents Pay",
                "to_chain": invoice.get("recipient_chain"),
                "to_address": invoice.get("recipient"),
                "to_label": invoice.get("recipient"),
                "token": invoice.get("token"),
                "amount": invoice.get("amount"),
                "memo": invoice.get("memo") or "",
                "status": invoice.get("status"),
                "status_label": invoice.get("status_label"),
                "created_at": invoice.get("created_at"),
                "updated_at": invoice.get("updated_at"),
                "paid_at": invoice.get("paid_at"),
                "explorer": invoice.get("explorer"),
                "badge": invoice.get("badge"),
                "fixture": bool(invoice.get("fixture")),
            }
        )
    return arcs


def sentence(invoices: list[dict[str, Any]]) -> str:
    """One clause for the summary. Empty when there is nothing to mention."""
    if not invoices:
        return ""
    pending = [item for item in invoices if item.get("pending")]
    paid = [item for item in invoices if item.get("paid")]
    bits: list[str] = []
    if pending:
        first = pending[0]
        extra = f" and {len(pending) - 1} more" if len(pending) > 1 else ""
        bits.append(
            f"{len(pending)} pending ({first['amount']} {first['token']} to {first['recipient']}{extra}, {first['status']})"
        )
    if paid:
        first = paid[0]
        extra = f" and {len(paid) - 1} more" if len(paid) > 1 else ""
        bits.append(f"{len(paid)} paid ({first.get('badge') or first['id']}{extra})")
    if not bits:
        closed = len(invoices)
        bits.append(f"{closed} closed")
    return "Intents Pay: " + "; ".join(bits) + "."


def _public_base(record: dict[str, Any]) -> dict[str, Any] | None:
    recipient = str(record.get("recipient") or "").strip()
    if not recipient:
        return None
    token = str(record.get("currency") or record.get("token") or "").strip().upper()
    if not token:
        return None
    recipient_chain = _chain_for(recipient, record.get("destination_chain") or "near")
    recipient_norm = _norm(recipient_chain, recipient) if recipient_chain else recipient
    deposit_raw = record.get("deposit_address")
    deposit = str(deposit_raw).strip() if deposit_raw else ""
    deposit_chain = _chain_for(deposit, str(record.get("origin_chain") or "")) if deposit else None
    deposit_norm = _norm(deposit_chain, deposit) if deposit and deposit_chain else (deposit or None)
    created = record.get("created_at")
    memo = str(record.get("memo") or "").strip()
    number = str(record.get("number") or record.get("id") or "").strip()
    identifier = str(record.get("id") or number).strip()
    if not identifier:
        return None
    explorer = ""
    if recipient_chain:
        explorer = explorer_address(recipient_chain, recipient_norm)
    elif deposit_chain and deposit_norm:
        explorer = explorer_address(deposit_chain, deposit_norm)
    return {
        "id": identifier,
        "number": number or identifier,
        "recipient": recipient_norm if recipient_chain else recipient,
        "recipient_chain": recipient_chain,
        "recipient_id": node_id(recipient_chain, recipient_norm) if recipient_chain else "",
        "deposit_address": deposit_norm,
        "deposit_chain": deposit_chain,
        "deposit_id": node_id(deposit_chain, deposit_norm) if deposit_chain and deposit_norm else "",
        "amount": _amount_text(record),
        "token": token,
        "memo": memo,
        "created_at": created,
        "updated_at": record.get("status_updated_at") or record.get("updated_at"),
        "paid_at": record.get("paid_at"),
        "deadline": record.get("deadline"),
        "dry": bool(record.get("dry", True)),
        "explorer": explorer,
        "fixture": False,
        "badge": "",
        "matched_flow_id": None,
        "matched_from_id": "",
        "matched_from": "",
        "matched_from_chain": "",
        "matched_from_label": "",
        "_expected": _expected_amounts(record),
    }


def _matching_flow(invoice: dict[str, Any], flows: list[dict[str, Any]]) -> dict[str, Any] | None:
    recipient = str(invoice.get("recipient") or "")
    chain = invoice.get("recipient_chain")
    expected: list[Decimal] = list(invoice.get("_expected") or [])
    if not recipient or not expected:
        return None
    best: dict[str, Any] | None = None
    for flow in flows:
        if chain and flow.get("chain") != chain:
            continue
        if _norm(chain, str(flow.get("dst") or "")) != recipient:
            continue
        if _norm(chain, str(flow.get("src") or "")) == recipient:
            continue
        if not _tokens_match(str(invoice.get("token") or ""), str(flow.get("token") or "")):
            continue
        actual = to_decimal(flow.get("amount_value") if flow.get("amount_value") not in (None, "") else flow.get("amount"))
        if not any(_amounts_close(want, actual) for want in expected):
            continue
        if best is None or int(flow.get("ts") or 0) >= int(best.get("ts") or 0):
            best = flow
    if best is not None:
        src_chain = str(best.get("chain") or "")
        src = str(best.get("src") or "")
        invoice["matched_from"] = src
        invoice["matched_from_chain"] = src_chain
        invoice["matched_from_label"] = str(best.get("src_label") or "")
        if src_chain and src:
            invoice["matched_from_id"] = node_id(src_chain, src)
    return best


def _iso(ts: object) -> str | None:
    try:
        stamp = int(ts)
    except (TypeError, ValueError):
        return None
    if stamp <= 0:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stamp))


def public_invoice(invoice: dict[str, Any]) -> dict[str, Any]:
    hidden = set(_HIDDEN) | {"_expected"}
    return {key: value for key, value in invoice.items() if key not in hidden}
