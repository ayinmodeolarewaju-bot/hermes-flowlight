"""Unit tests with mocked chain responses. No network."""

from __future__ import annotations

import json
from pathlib import Path

import flowlight_plugin.cli as cli
import flowlight_plugin.narrate as narrate
import flowlight_plugin.parse as parse
import flowlight_plugin.providers as providers
import flowlight_plugin.service as service
import flowlight_plugin.tools as tools
from flowlight_plugin.httpclient import HttpError
from flowlight_plugin.runtime import Deps, Settings
from flowlight_plugin.store import Store

ROOT = Path(__file__).resolve().parents[1]
BUSY = "0x9c955c40dc98fce89a133f402ffbf94070e6e299"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
VITALIK = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"


def deps(fetcher=None, **overrides):
    return Deps(
        http=overrides.get("http"),
        store=overrides.get("store") or Store(None),
        settings=overrides.get("settings") or Settings(demo_mode=False),
        now=overrides.get("now") or (lambda: 1_700_000_000),
        fetcher=fetcher,
        ledger_path=overrides.get("ledger_path"),
    )


def test_parse_mixed_phrase_and_reject_seed():
    found = parse.parse_watch_text("purefile1686.near and 0x" + "ab" * 20 + " on Base")
    assert found[0] == {"address": "purefile1686.near", "chain": "near"}
    assert found[1]["chain"] == "base"
    assert found[1]["address"].startswith("0xab")
    try:
        parse.parse_watch_text("abandon ability able about above absent absorb abstract absurd abuse access accident")
        raise AssertionError("seed phrase should be refused")
    except parse.InputError as exc:
        assert "read-only" in str(exc).lower() or "seed" in str(exc).lower()
    try:
        parse.parse_watch_text("0x" + "ab" * 20)
        raise AssertionError("bare evm address needs a chain")
    except parse.InputError:
        pass


def test_blockscout_and_log_normalization():
    prices = {"USDC": 1.0, "ETH": 2000.0}
    items = [{
        "from": {"hash": "0x" + "11" * 20, "ens_domain_name": "alice.eth"},
        "to": {"hash": BUSY, "name": "Busy"},
        "token": {"symbol": "USDC", "decimals": "6", "type": "ERC-20"},
        "total": {"value": "18420000000", "decimals": "6"},
        "timestamp": "2026-11-09T22:00:00Z",
        "transaction_hash": "0x" + "aa" * 32,
        "log_index": 3,
    }, {
        "_native": True,
        "from": {"hash": BUSY},
        "to": {"hash": "0x" + "22" * 20},
        "value": "1000000000000000000",
        "timestamp": "2026-11-09T22:05:00Z",
        "hash": "0x" + "bb" * 32,
        "status": "ok",
    }]
    flows = providers.flows_from_blockscout("base", BUSY, items, prices)
    assert len(flows) == 2
    assert flows[0]["amount"] == "18,420"
    assert flows[0]["usd"] == 18420
    assert flows[0]["src_label"] == "alice.eth"
    assert flows[0]["explorer"].startswith("https://base.blockscout.com/tx/")
    assert flows[1]["token"] == "ETH"
    assert flows[1]["amount"] == "1"
    log = {
        "topics": [
            providers.TRANSFER_TOPIC,
            "0x" + BUSY[2:].rjust(64, "0"),
            "0x" + "33" * 20,
        ],
        "data": hex(2_500_000),
        "transactionHash": "0x" + "cc" * 32,
        "logIndex": "0x4",
        "blockTimestamp": hex(1_700_000_100),
        "removed": False,
    }
    logged = providers.flows_from_logs("base", "USDC", 6, [log], prices)
    assert logged[0]["amount"] == "2.5"
    assert logged[0]["src"] == BUSY
    assert logged[0]["ts"] == 1_700_000_100


def test_near_signed_delta_direction():
    class Fake:
        def get_json(self, url, **kwargs):
            if url.endswith("ft-txns?per_page=25"):
                return {"txns": [{
                    "cause": "TRANSFER",
                    "delta_amount": "-250000000",
                    "involved_account_id": "intents.near",
                    "affected_account_id": "purefile1686.near",
                    "transaction_hash": "nearhash",
                    "block_timestamp": "1700000000000000000",
                    "event_index": "1",
                    "ft": {"symbol": "USDC", "decimals": 6},
                }, {
                    "cause": "BURN",
                    "delta_amount": "-1",
                    "ft": {"symbol": "USDC", "decimals": 6},
                    "transaction_hash": "burn",
                    "block_timestamp": "1700000000000000000",
                }]}
            return {"txns": [{
                "predecessor_account_id": "wrap.near",
                "receiver_account_id": "purefile1686.near",
                "transaction_hash": "nativehash",
                "block_timestamp": "1700000100000000000",
                "actions": [{"action": "TRANSFER", "deposit": "2000000000000000000000000"}, {"action": "ADD_KEY", "deposit": 0}],
            }]}

    flows, warnings = providers.fetch_near(
        "purefile1686.near", Fake(), {"USDC": 1, "NEAR": 2}, deadline=10**12, cap=20
    )
    assert warnings == []
    usdc = next(flow for flow in flows if flow["token"] == "USDC")
    assert usdc["src"] == "purefile1686.near"
    assert usdc["dst"] == "intents.near"
    assert usdc["amount"] == "250"
    native = next(flow for flow in flows if flow["token"] == "NEAR")
    assert native["src"] == "wrap.near"
    assert native["dst"] == "purefile1686.near"
    assert native["amount"] == "2"


def test_shared_inflow_is_toward_the_watched_address_and_matches_everywhere():
    from decimal import Decimal

    from flowlight_plugin.money import format_amount
    import flowlight_plugin.service as service_mod

    assert format_amount(Decimal("152156.87")) == "152,156.87"
    assert format_amount(Decimal("18420")) == "18,420"
    hub = "0x" + "aa" * 20
    other = "0x" + "bb" * 20
    second = "0x" + "cc" * 20
    watches = [
        {"chain": "base", "address": hub, "label": "Hub"},
        {"chain": "base", "address": second, "label": "Second"},
    ]
    flows = [
        {
            "id": "out", "chain": "base", "token": "USDC",
            "amount": format_amount(Decimal("9000000")), "amount_value": 9_000_000, "usd": 9_000_000,
            "ts": 3, "src": hub, "dst": other, "explorer": "https://example.test/out",
            "src_label": "Hub", "dst_label": "exit",
        },
        {
            "id": "internal", "chain": "base", "token": "USDC",
            "amount": format_amount(Decimal("8000000")), "amount_value": 8_000_000, "usd": 8_000_000,
            "ts": 4, "src": hub, "dst": second, "explorer": "https://example.test/internal",
            "src_label": "Hub", "dst_label": "Second",
        },
        {
            "id": "small-in", "chain": "base", "token": "USDC",
            "amount": format_amount(Decimal("1000")), "amount_value": 1000, "usd": 1000,
            "ts": 1, "src": other, "dst": hub, "explorer": "https://example.test/small",
            "src_label": "desk", "dst_label": "Hub",
        },
        {
            "id": "big-in", "chain": "base", "token": "USDC",
            "amount": format_amount(Decimal("152156.87")), "amount_value": 152156.87, "usd": 152156.87,
            "ts": 2, "src": other, "dst": hub, "explorer": "https://example.test/big",
            "src_label": "whale", "dst_label": "Hub",
        },
    ]
    annotated = service_mod._annotate(flows, watches)
    assert next(row for row in annotated if row["id"] == "big-in")["direction"] == "in"
    assert next(row for row in annotated if row["id"] == "out")["direction"] == "out"
    assert next(row for row in annotated if row["id"] == "internal")["direction"] == "internal"
    summary = narrate.summarize(annotated, watches, requested_hours=24, warnings=[])
    assert summary["largest_inflow"]["id"] == "big-in"
    assert summary["largest_inflow"]["amount"] == "152,156.87"
    from flowlight_plugin.money import format_usd
    assert summary["headline"] == (
        "Largest inflow 152,156.87 USDC (" + format_usd(152156.87) + ") · 4 transfers in the scanned window."
    )
    assert summary["headline"] in summary["text"]
    assert "9,000,000" not in summary["headline"]
    assert "8,000,000" not in summary["headline"]
    box = deps(fetcher=lambda _watches, _deps: (annotated, []))
    for watch in watches:
        box.store.upsert({**watch, "added_at": 1})
    picture = service.graph(box)
    assert picture["summary"]["headline"] == summary["headline"]
    assert picture["summary"]["largest_inflow"]["amount"] == picture["summary"]["headline"].split(" ")[2]


def test_summary_picks_largest_and_admits_a_short_window():
    watches = [{"chain": "base", "address": BUSY, "label": "Busy"}]
    flows = [
        {"chain": "base", "src": "0x" + "11" * 20, "dst": BUSY, "token": "USDC", "amount": "10",
         "amount_value": 10, "usd": 10, "ts": 1_000, "direction": "in", "explorer": "https://example.test/in",
         "src_label": "desk", "dst_label": "Busy"},
        {"chain": "base", "src": "0x" + "22" * 20, "dst": BUSY, "token": "USDC", "amount": "90",
         "amount_value": 90, "usd": 90, "ts": 2_000, "direction": "in", "explorer": "https://example.test/big",
         "src_label": "whale", "dst_label": "Busy"},
        {"chain": "base", "src": BUSY, "dst": "0x" + "33" * 20, "token": "USDC", "amount": "5",
         "amount_value": 5, "usd": 5, "ts": 1_500, "direction": "out", "explorer": "https://example.test/out",
         "src_label": "Busy", "dst_label": "exit"},
    ]
    summary = narrate.summarize(flows, watches, requested_hours=24, warnings=[])
    assert summary["largest_inflow"]["amount"] == "90"
    assert "https://example.test/big" in summary["text"]
    assert summary["complete"] is False
    assert "shorter than the requested 24h" in summary["text"]
    assert summary["in_usd"] == 100
    assert summary["out_usd"] == 5


def test_watch_unwatch_and_tool_json(tmp_path):
    store = Store(tmp_path / "watches.json")
    seen = {}

    def fetcher(watches, _deps):
        seen["n"] = len(watches)
        base = next(item for item in watches if item["chain"] == "base")
        return ([{
            "id": "base:tx:1",
            "chain": "base",
            "token": "USDC",
            "amount": "4",
            "amount_value": 4,
            "usd": 4,
            "ts": 1_700_000_000,
            "src": "0x" + "11" * 20,
            "dst": base["address"],
            "tx": "0x" + "ab" * 32,
            "explorer": "https://base.blockscout.com/tx/0x" + "ab" * 32,
            "source": "test",
            "src_label": "desk",
            "dst_label": base["label"],
        }], ["base: sample warning"])

    box = deps(fetcher=fetcher, store=store)
    added = service.watch_accounts({"text": f"purefile1686.near and {BUSY} on Base"}, box)
    assert added["ok"] is True
    assert added["demo"] is False
    assert added["funds_moved"] is False
    assert len(added["added"]) == 2
    assert seen["n"] == 2
    assert any(node["watched"] and node["chain"] == "near" for node in added["nodes"])
    assert "Largest inflow" in added["summary"]["text"]
    listed = json.loads(tools.flowlight_list({}, _deps=box))
    assert listed["count"] == 2
    removed = service.unwatch_accounts({"text": "purefile1686.near"}, box)
    assert removed["removed"][0]["address"] == "purefile1686.near"
    assert len(store.list_watches()) == 1
    refused = json.loads(tools.flowlight_watch({"text": "here is my private key"}, _deps=box))
    assert refused["ok"] is False


def test_demo_fixture_is_labeled_and_live_flag_wins():
    box = deps(settings=Settings(demo_mode=True))
    demo = service.graph(box)
    assert demo["demo"] is True
    assert demo["mode"] == "demo"
    assert "DEMO FIXTURE" in demo["summary"]["text"]
    assert demo["flows"]
    live = service.graph(box, live=True)
    assert live["demo"] is False
    assert live["flows"] == []


def test_slash_and_cli_parse():
    action, args = cli.parse_slash("watch purefile1686.near and 0x" + "cd" * 20 + " on Base")
    assert action == "watch"
    assert "purefile1686.near" in args["text"]
    assert cli.parse_slash("")[0] is None
    assert cli.parse_slash("demo")[1]["demo"] is True


def test_http_client_caches_and_backs_off():
    calls = {"n": 0}

    def transport(method, url, body, headers, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            return 429, b""
        return 200, b'{"ok": true, "n": %d}' % calls["n"]

    client = providers_http(transport)
    first = client.get_json("https://example.test/v1", ttl=60, timeout=1)
    assert first["ok"] is True
    again = client.get_json("https://example.test/v1", ttl=60, timeout=1)
    assert again == first
    assert calls["n"] == 2

    def always_down(method, url, body, headers, timeout):
        return 403, b"no"
    blocked = providers_http(always_down)
    try:
        blocked.get_json("https://blocked.test/x", ttl=0, timeout=1)
        raise AssertionError("403 should fail")
    except HttpError as exc:
        assert exc.status == 403
    assert blocked.is_down("https://blocked.test/x")


def providers_http(transport):
    from flowlight_plugin.httpclient import HttpClient
    return HttpClient(transport, pause=0, sleeper=lambda _seconds: None)


def test_solana_parsed_transfer():
    tx = {
        "blockTime": 1_700_000_000,
        "meta": {"err": None},
        "transaction": {"message": {"instructions": [{
            "parsed": {
                "type": "transfer",
                "info": {"source": "Desk11111111111111111111111111111111111", "destination": "Dest11111111111111111111111111111111111", "lamports": 2_000_000_000},
            }
        }]}},
    }
    flows = providers._solana_flows("Desk11111111111111111111111111111111111", "sig", tx, {"SOL": 100})
    assert flows[0]["token"] == "SOL"
    assert flows[0]["amount"] == "2"
    assert flows[0]["usd"] == 200


def _ledger(path: Path, invoices: list) -> Path:
    path.write_text(json.dumps({"invoices": invoices, "pending": {}}), encoding="utf-8")
    return path


def _near_invoice(**overrides):
    row = {
        "id": "ip_abc123",
        "number": "IP-20261110-ABCD",
        "kind": "invoice",
        "created_at": "2026-11-10T00:00:00Z",
        "amount": "25",
        "currency": "USDC",
        "recipient": "purefile1686.near",
        "memo": "design sprint",
        "origin_chain": "arb",
        "dry": True,
        "deposit_address": None,
        "payment_status": "DRY_QUOTE",
        "funds_moved": False,
    }
    row.update(overrides)
    return row


class _StatusHttp:
    def __init__(self, body):
        self.body = body
        self.urls = []

    def get_json_once(self, url, timeout=4):
        self.urls.append(url)
        if isinstance(self.body, Exception):
            raise self.body
        return self.body


def test_invoice_ledger_missing_malformed_pending_and_paid(tmp_path):
    from flowlight_plugin import invoices as invoice_book

    invoice_book.clear_status_cache()
    missing = deps(ledger_path=tmp_path / "missing.json")
    quiet = service.invoice_report({}, missing)
    assert quiet["invoices"] == []
    assert quiet["note"] == "no Intents Pay invoices found"
    assert quiet["funds_moved"] is False
    assert quiet["read_only"] is True
    assert "Intents Pay" not in service.graph(missing)["summary"]["text"]

    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    broken = service.graph(deps(ledger_path=bad))
    assert broken["invoices"] == []
    assert broken["invoice_note"] == "no Intents Pay invoices found"
    assert broken["ledger"] == "malformed"
    assert any("could not be read" in item for item in broken["warnings"])
    assert bad.read_text(encoding="utf-8") == "{"

    deposit = "0x" + "ab" * 20
    pending = _near_invoice()
    paid = _near_invoice(
        id="ip_paid",
        number="IP-PAID",
        amount="250",
        payment_status="SUCCESS",
        dry=False,
        deposit_address=deposit,
        memo="settled",
    )
    refunded = _near_invoice(
        id="ip_refund",
        number="IP-REFUND",
        amount="10",
        payment_status="REFUNDED",
        dry=False,
        deposit_address="0x" + "cd" * 20,
    )
    waiting = _near_invoice(id="ip_wait", number="IP-WAIT", amount="7", memo="still open")
    path = _ledger(tmp_path / "ledger.json", [pending, paid, refunded, waiting, {"memo": "no recipient"}])
    before = path.read_text(encoding="utf-8")

    def fetcher(watches, _deps):
        return ([{
            "id": "near:in",
            "chain": "near",
            "token": "USDC",
            "amount": "25",
            "amount_value": 25,
            "usd": 25,
            "ts": 1_700_000_100,
            "src": "intents.near",
            "dst": "purefile1686.near",
            "src_label": "NEAR Intents",
            "dst_label": "purefile1686.near",
            "explorer": "https://nearblocks.io/txns/example",
        }, {
            "id": "near:out",
            "chain": "near",
            "token": "USDC",
            "amount": "10",
            "amount_value": 10,
            "usd": 10,
            "ts": 1_700_000_200,
            "src": "purefile1686.near",
            "dst": "someone.near",
            "explorer": "https://nearblocks.io/txns/out",
        }], [])

    box = deps(fetcher=fetcher, ledger_path=path)
    picture = service.graph(box)
    assert path.read_text(encoding="utf-8") == before
    by_id = {item["id"]: item for item in picture["invoices"]}
    assert by_id["ip_abc123"]["pending"] is False
    assert by_id["ip_abc123"]["paid"] is True
    assert by_id["ip_abc123"]["status_source"] == "on-chain"
    assert by_id["ip_abc123"]["badge"] == "invoice IP-20261110-ABCD paid · 25 USDC"
    assert by_id["ip_paid"]["paid"] is True
    assert by_id["ip_paid"]["status_source"] == "ledger"
    assert by_id["ip_refund"]["paid"] is False
    assert by_id["ip_refund"]["pending"] is False
    assert by_id["ip_wait"]["pending"] is True
    assert by_id["ip_wait"]["paid"] is False
    assert by_id["ip_wait"]["status"] == "DRY_QUOTE"
    assert "signature" not in by_id["ip_paid"]
    assert any(item["address"] == "purefile1686.near" for item in picture["watches"])
    assert any(item["chain"] == "arbitrum" and item["address"] == deposit for item in picture["watches"])
    assert any(arc["badge"].startswith("invoice IP-20261110-ABCD paid") for arc in picture["invoice_arcs"])
    assert "Intents Pay:" in picture["summary"]["text"]
    listed = json.loads(tools.flowlight_invoices({}, _deps=box))
    assert listed["ok"] is True
    assert listed["funds_moved"] is False
    assert any(item["id"] == "ip_abc123" for item in listed["invoices"])


def test_invoice_status_get_marks_paid_without_writing(tmp_path):
    from flowlight_plugin import invoices as invoice_book

    invoice_book.clear_status_cache()
    deposit = "0x" + "11" * 20
    path = _ledger(tmp_path / "ledger.json", [
        _near_invoice(payment_status="PENDING_DEPOSIT", dry=False, deposit_address=deposit, amount="40"),
    ])
    http = _StatusHttp({"status": "SUCCESS", "updatedAt": "2026-11-10T01:02:03Z"})
    box = deps(http=http, ledger_path=path, fetcher=lambda _watches, _deps: ([], []))
    picture = service.graph(box)
    invoice = picture["invoices"][0]
    assert invoice["paid"] is True
    assert invoice["status"] == "SUCCESS"
    assert invoice["status_source"] == "1click"
    assert invoice["updated_at"] == "2026-11-10T01:02:03Z"
    assert http.urls and "depositAddress=" in http.urls[0]
    assert "1click.chaindefuser.com/v0/status" in http.urls[0]
    assert json.loads(path.read_text(encoding="utf-8"))["invoices"][0]["payment_status"] == "PENDING_DEPOSIT"


def test_demo_invoices_are_labeled_and_phase_filters():
    box = deps()
    demo = service.graph(box, demo=True)
    assert demo["ledger"] == "fixture"
    assert any(item["fixture"] and item["pending"] and item["amount"] == "25" for item in demo["invoices"])
    assert any(item["fixture"] and item["paid"] for item in demo["invoices"])
    assert demo["invoice_arcs"][0]["fixture"] is True
    assert "DEMO FIXTURE" in demo["summary"]["text"]
    assert "Intents Pay:" in demo["summary"]["text"]
    pending = service.graph(box, demo=True, phase="pending")
    assert pending["invoice_arcs"] == []
    assert all(item["pending"] for item in pending["invoices"])
    paid = service.graph(box, demo=True, phase="paid")
    assert paid["invoice_arcs"]
    assert all(item["paid"] for item in paid["invoices"])
    raw = json.loads(tools.flowlight_invoices({"demo": True}, _deps=box))
    assert raw["demo"] is True
    assert "DEMO FIXTURE" in raw["summary"]["text"]
    action, args = cli.parse_slash("invoices")
    assert action == "invoices"
    assert args["demo"] is False
    assert cli.parse_slash("invoices demo")[1]["demo"] is True


def test_frontend_bundle_contains_engine_and_avoids_desktop_pitfalls():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bundle_frontend", ROOT / "scripts" / "bundle_frontend.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    module.build()
    assert module.check() == 0
    desktop = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
    dashboard = (ROOT / "dashboard" / "dist" / "index.js").read_text(encoding="utf-8")
    engine = (ROOT / "frontend" / "engine.js").read_text(encoding="utf-8")
    assert "summary.headline" in engine
    assert "top:74px" not in engine
    assert "function mountFlowlight" in desktop
    assert "function mountFlowlight" in dashboard
    assert "FLOWLIGHT" in engine
    for banned in ("eval(", "new Function", "createElement('script'", 'createElement("script"', "<script"):
        assert banned not in desktop
    assert 'from "@hermes/plugin-sdk"' in desktop or "from '@hermes/plugin-sdk'" in desktop
