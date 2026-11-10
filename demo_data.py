"""Offline fixture. Every response that uses it is labeled demo."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from .chains import explorer_address, explorer_tx, node_id
from .money import format_amount
from .narrate import summarize

# Relative minutes keep the scrubber inside "now" whenever the fixture is built.
_ROWS: list[dict[str, Any]] = [
    {"chain": "base", "token": "USDC", "amount": 18420, "usd": 18411.2, "minutes": 18, "src": "0x1111111111111111111111111111111111111111", "dst": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "src_label": "Demo desk A", "dst_label": "Busy Base"},
    {"chain": "base", "token": "USDC", "amount": 9600, "usd": 9595.4, "minutes": 26, "src": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "dst": "0x2222222222222222222222222222222222222222", "src_label": "Busy Base", "dst_label": "Demo desk B"},
    {"chain": "base", "token": "USDC", "amount": 4200, "usd": 4198.1, "minutes": 41, "src": "0x3333333333333333333333333333333333333333", "dst": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "src_label": "Demo desk C", "dst_label": "Busy Base"},
    {"chain": "base", "token": "WETH", "amount": 1.25, "usd": 2662.5, "minutes": 55, "src": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "dst": "0x4200000000000000000000000000000000000006", "src_label": "Busy Base", "dst_label": "WETH"},
    {"chain": "base", "token": "USDC", "amount": 2750, "usd": 2748.6, "minutes": 70, "src": "0x4444444444444444444444444444444444444444", "dst": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "src_label": "Demo desk D", "dst_label": "Busy Base"},
    {"chain": "base", "token": "AERO", "amount": 18000, "usd": 16200, "minutes": 84, "src": "0x5555555555555555555555555555555555555555", "dst": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "src_label": "Demo pool", "dst_label": "Busy Base"},
    {"chain": "base", "token": "USDC", "amount": 880, "usd": 879.5, "minutes": 96, "src": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "dst": "0x6666666666666666666666666666666666666666", "src_label": "Busy Base", "dst_label": "Demo desk E"},
    {"chain": "base", "token": "USDC", "amount": 15440, "usd": 15432.0, "minutes": 110, "src": "0x7777777777777777777777777777777777777777", "dst": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "src_label": "Demo desk F", "dst_label": "Busy Base"},
    {"chain": "near", "token": "wNEAR", "amount": 120, "usd": 433.2, "minutes": 34, "src": "wrap.near", "dst": "purefile1686.near", "src_label": "wNEAR", "dst_label": "purefile1686.near"},
    {"chain": "near", "token": "USDC", "amount": 250, "usd": 249.9, "minutes": 62, "src": "intents.near", "dst": "purefile1686.near", "src_label": "NEAR Intents", "dst_label": "purefile1686.near"},
    {"chain": "near", "token": "USDC", "amount": 80, "usd": 79.9, "minutes": 140, "src": "purefile1686.near", "dst": "intents.near", "src_label": "purefile1686.near", "dst_label": "NEAR Intents"},
    {"chain": "near", "token": "NEAR", "amount": 40, "usd": 144.4, "minutes": 200, "src": "relay.near", "dst": "purefile1686.near", "src_label": "relay.near", "dst_label": "purefile1686.near"},
]


def demo_watches() -> list[dict[str, Any]]:
    return [
        {"chain": "near", "address": "purefile1686.near", "label": "purefile1686.near"},
        {"chain": "base", "address": "0x9c955c40dc98fce89a133f402ffbf94070e6e299", "label": "Busy Base"},
    ]


def demo_invoices(now: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Labeled fixture invoices. They are not read from an Intents Pay ledger."""
    created = datetime.fromtimestamp(now - 3600, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    settled = datetime.fromtimestamp(now - 180, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    recipient = "purefile1686.near"
    recipient_id = node_id("near", recipient)
    explorer = explorer_address("near", recipient)
    pending = {
        "id": "ip_demo_pending",
        "number": "IP-DEMO-PEND",
        "recipient": recipient,
        "recipient_chain": "near",
        "recipient_id": recipient_id,
        "deposit_address": None,
        "deposit_chain": None,
        "deposit_id": "",
        "amount": "25",
        "token": "USDC",
        "memo": "design sprint",
        "status": "DRY_QUOTE",
        "status_label": "Dry quote only. There is no deposit to track.",
        "status_source": "fixture",
        "paid": False,
        "pending": True,
        "created_at": created,
        "updated_at": None,
        "paid_at": None,
        "deadline": None,
        "dry": True,
        "explorer": explorer,
        "fixture": True,
        "badge": "",
        "matched_flow_id": None,
    }
    badge = "invoice IP-DEMO-PAID paid · 250 USDC"
    paid = {
        "id": "ip_demo_paid",
        "number": "IP-DEMO-PAID",
        "recipient": recipient,
        "recipient_chain": "near",
        "recipient_id": recipient_id,
        "deposit_address": None,
        "deposit_chain": None,
        "deposit_id": "",
        "amount": "250",
        "token": "USDC",
        "memo": "fixture settlement",
        "status": "SUCCESS",
        "status_label": "Payment settled",
        "status_source": "fixture",
        "paid": True,
        "pending": False,
        "created_at": created,
        "updated_at": settled,
        "paid_at": settled,
        "deadline": None,
        "dry": True,
        "explorer": explorer,
        "fixture": True,
        "badge": badge,
        "matched_flow_id": "demo:9",
    }
    arc = {
        "id": "invoice:ip_demo_paid",
        "invoice_id": "ip_demo_paid",
        "number": "IP-DEMO-PAID",
        "from_id": node_id("near", "intents-pay.near"),
        "to_id": recipient_id,
        "from_chain": "near",
        "from_address": "intents-pay.near",
        "from_label": "Intents Pay",
        "to_chain": "near",
        "to_address": recipient,
        "to_label": recipient,
        "token": "USDC",
        "amount": "250",
        "memo": "fixture settlement",
        "status": "SUCCESS",
        "status_label": "Payment settled",
        "created_at": created,
        "updated_at": settled,
        "paid_at": settled,
        "explorer": explorer,
        "badge": badge,
        "fixture": True,
    }
    return [pending, paid], [arc]


def build_demo(now: float) -> dict[str, Any]:
    flows = []
    nodes: dict[str, dict[str, Any]] = {}
    for watch in demo_watches():
        nodes[node_id(watch["chain"], watch["address"])] = {
            "id": node_id(watch["chain"], watch["address"]),
            "chain": watch["chain"],
            "address": watch["address"],
            "label": watch["label"],
            "watched": True,
            "kind": "account",
            "explorer": explorer_address(watch["chain"], watch["address"]),
        }
    for index, row in enumerate(_ROWS):
        ts = int(now - int(row["minutes"]) * 60)
        flow = {
            "id": f"demo:{index}",
            "chain": row["chain"],
            "token": row["token"],
            "amount": format_amount(Decimal(str(row["amount"]))),
            "amount_value": float(row["amount"]),
            "usd": float(row["usd"]),
            "ts": ts,
            "src": row["src"],
            "dst": row["dst"],
            "src_label": row["src_label"],
            "dst_label": row["dst_label"],
            "tx": f"demo-tx-{index}",
            "explorer": explorer_tx(row["chain"], f"demo-tx-{index}"),
            "source": "demo-fixture",
            "direction": "in" if row["dst"] in {item["address"] for item in demo_watches()} else "out",
        }
        # Internal NEAR payout from purefile is out; arrivals are in. The check above
        # treats any watched destination as inflow, including a transfer between watches.
        if row["src"] in {item["address"] for item in demo_watches()} and row["dst"] in {item["address"] for item in demo_watches()}:
            flow["direction"] = "internal"
        elif row["src"] in {item["address"] for item in demo_watches()}:
            flow["direction"] = "out"
        flows.append(flow)
        for side, label_key in (("src", "src_label"), ("dst", "dst_label")):
            address = row[side]
            ident = node_id(row["chain"], address)
            watched = any(item["address"] == address and item["chain"] == row["chain"] for item in demo_watches())
            nodes.setdefault(ident, {
                "id": ident,
                "chain": row["chain"],
                "address": address,
                "label": row[label_key],
                "watched": watched,
                "kind": "account",
                "explorer": explorer_address(row["chain"], address),
            })
    flows.sort(key=lambda item: item["ts"], reverse=True)
    nodes.setdefault(node_id("near", "intents-pay.near"), {
        "id": node_id("near", "intents-pay.near"),
        "chain": "near",
        "address": "intents-pay.near",
        "label": "Intents Pay",
        "watched": False,
        "kind": "account",
        "explorer": explorer_address("near", "intents-pay.near"),
    })
    invoice_rows, arcs = demo_invoices(now)
    summary = summarize(
        flows,
        demo_watches(),
        requested_hours=24,
        warnings=["Showing the built-in demo fixture. These transfers were not read from a chain."],
    )
    pending_n = sum(1 for item in invoice_rows if item["pending"])
    paid_n = sum(1 for item in invoice_rows if item["paid"])
    summary["text"] = (
        "DEMO FIXTURE, not live chain data. "
        + summary["text"]
        + f" Intents Pay: {pending_n} pending (25 USDC to purefile1686.near, DRY_QUOTE); "
        + f"{paid_n} paid (invoice IP-DEMO-PAID paid · 250 USDC)."
    )
    summary["label"] = "DEMO FIXTURE"
    summary["invoice_pending"] = pending_n
    summary["invoice_paid"] = paid_n
    return {
        "ok": True,
        "demo": True,
        "mode": "demo",
        "read_only": True,
        "funds_moved": False,
        "signing": False,
        "warnings": ["Showing the built-in demo fixture. These transfers were not read from a chain."],
        "watches": demo_watches(),
        "flows": flows,
        "nodes": list(nodes.values()),
        "summary": summary,
        "invoices": invoice_rows,
        "invoice_arcs": arcs,
        "invoice_note": "",
        "ledger": "fixture",
    }
