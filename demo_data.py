"""Offline fixture. Every response that uses it is labeled demo."""

from __future__ import annotations

from typing import Any

from decimal import Decimal

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
    summary = summarize(
        flows,
        demo_watches(),
        requested_hours=24,
        warnings=["Showing the built-in demo fixture. These transfers were not read from a chain."],
    )
    summary["text"] = "DEMO FIXTURE, not live chain data. " + summary["text"]
    summary["label"] = "DEMO FIXTURE"
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
    }
