"""Read public transfer feeds. Every function returns flows plus warnings."""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

from .chains import (
    CHAINS,
    TOKENS,
    TRANSFER_TOPIC,
    explorer_tx,
    known_label,
    normalize_address,
)
from .httpclient import HttpClient, HttpError
from .money import format_amount, from_base_units, parse_time, price_symbol, to_decimal, usd_value

Flow = dict[str, Any]


def _flow(
    *,
    chain: str,
    token: str,
    raw: object,
    decimals: int,
    ts: int | None,
    src: str,
    dst: str,
    tx: str,
    log_index: object = 0,
    src_label: str | None = None,
    dst_label: str | None = None,
    source: str,
    prices: dict[str, float],
) -> Flow | None:
    if not src or not dst or not tx or ts is None:
        return None
    amount = from_base_units(raw, decimals)
    if amount == 0:
        return None
    src_n = normalize_address(chain, src)
    dst_n = normalize_address(chain, dst)
    symbol = token or "TOKEN"
    return {
        "id": f"{chain}:{tx}:{log_index}",
        "chain": chain,
        "token": symbol,
        "amount": format_amount(amount),
        "amount_value": float(amount),
        "usd": usd_value(symbol, amount, prices),
        "ts": int(ts),
        "src": src_n,
        "dst": dst_n,
        "src_label": src_label or known_label(chain, src_n),
        "dst_label": dst_label or known_label(chain, dst_n),
        "tx": tx,
        "explorer": explorer_tx(chain, tx),
        "source": source,
    }


def _name_from_party(party: object) -> str | None:
    if not isinstance(party, dict):
        return None
    ens = party.get("ens_domain_name")
    if isinstance(ens, str) and ens.strip():
        return ens.strip()
    name = party.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    meta = party.get("metadata") if isinstance(party.get("metadata"), dict) else {}
    for tag in meta.get("tags") or []:
        if isinstance(tag, dict) and tag.get("tagType") == "name" and tag.get("name"):
            return str(tag["name"])
    return None


def _party_hash(party: object) -> str:
    if isinstance(party, dict):
        return str(party.get("hash") or party.get("address") or "")
    return str(party or "")


def fetch_prices(http: HttpClient, symbols: set[str]) -> dict[str, float]:
    ids: dict[str, str] = {}
    for symbol in symbols:
        key = price_symbol(symbol)
        cg = {
            "ETH": "ethereum",
            "NEAR": "near",
            "SOL": "solana",
            "BTC": "bitcoin",
            "USDC": "usd-coin",
            "USDT": "tether",
            "DAI": "dai",
        }.get(key)
        if cg:
            ids[key] = cg
    prices: dict[str, float] = {"USDC": 1.0, "USDT": 1.0, "DAI": 1.0}
    if not ids:
        return prices
    url = (
        "https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids="
        + ",".join(sorted(set(ids.values())))
    )
    try:
        payload = http.get_json(url, ttl=600, timeout=8)
    except HttpError:
        return prices
    if not isinstance(payload, dict):
        return prices
    for key, cg in ids.items():
        row = payload.get(cg)
        if isinstance(row, dict) and row.get("usd") is not None:
            try:
                prices[key] = float(row["usd"])
            except (TypeError, ValueError):
                continue
    return prices


def _blockscout_pages(http: HttpClient, base: str, address: str, deadline: float, cap: int) -> list[dict] | None:
    """Return token-transfer items, or None when the explorer cannot be used."""
    if http.is_down(base):
        return None
    items: list[dict] = []
    params: dict[str, Any] = {"type": "ERC-20"}
    for _page in range(3):
        if time.monotonic() > deadline or len(items) >= cap:
            break
        url = f"{base}/api/v2/addresses/{address}/token-transfers?{urlencode(params)}"
        try:
            payload = http.get_json(url, ttl=40, timeout=8)
        except HttpError:
            return None if not items else items
        if not isinstance(payload, dict):
            return None if not items else items
        page_items = payload.get("items")
        if not isinstance(page_items, list):
            return None if not items else items
        items.extend(item for item in page_items if isinstance(item, dict))
        nxt = payload.get("next_page_params")
        if not isinstance(nxt, dict) or not nxt:
            break
        params = {"type": "ERC-20"}
        params.update({key: value for key, value in nxt.items() if value is not None})
    native_url = f"{base}/api/v2/addresses/{address}/transactions"
    if time.monotonic() < deadline:
        try:
            native = http.get_json(native_url, ttl=40, timeout=8)
        except HttpError:
            native = None
        if isinstance(native, dict) and isinstance(native.get("items"), list):
            for item in native["items"]:
                if isinstance(item, dict):
                    item = dict(item)
                    item["_native"] = True
                    items.append(item)
    return items


def flows_from_blockscout(chain: str, address: str, items: list[dict], prices: dict[str, float]) -> list[Flow]:
    meta = CHAINS[chain]
    flows: list[Flow] = []
    watched = normalize_address(chain, address)
    for item in items:
        if item.get("_native"):
            value = item.get("value")
            if to_decimal(value) <= 0:
                continue
            if str(item.get("status") or "ok").lower() in {"error", "reverted"}:
                continue
            flow = _flow(
                chain=chain,
                token=meta["native"],
                raw=value,
                decimals=18,
                ts=parse_time(item.get("timestamp")),
                src=_party_hash(item.get("from")),
                dst=_party_hash(item.get("to")),
                tx=str(item.get("hash") or ""),
                log_index="native",
                src_label=_name_from_party(item.get("from")),
                dst_label=_name_from_party(item.get("to")),
                source="blockscout",
                prices=prices,
            )
        else:
            token = item.get("token") if isinstance(item.get("token"), dict) else {}
            if str(token.get("type") or item.get("token_type") or "ERC-20").upper() not in {"ERC-20", "TOKEN"}:
                continue
            total = item.get("total") if isinstance(item.get("total"), dict) else {}
            decimals = int(to_decimal(token.get("decimals") or total.get("decimals") or 18))
            flow = _flow(
                chain=chain,
                token=str(token.get("symbol") or "TOKEN"),
                raw=total.get("value"),
                decimals=decimals,
                ts=parse_time(item.get("timestamp")),
                src=_party_hash(item.get("from")),
                dst=_party_hash(item.get("to")),
                tx=str(item.get("transaction_hash") or item.get("tx_hash") or ""),
                log_index=item.get("log_index") or 0,
                src_label=_name_from_party(item.get("from")),
                dst_label=_name_from_party(item.get("to")),
                source="blockscout",
                prices=prices,
            )
        if flow and (flow["src"] == watched or flow["dst"] == watched):
            flows.append(flow)
    return flows


def _rpc(http: HttpClient, urls: list[str], method: str, params: list, deadline: float) -> Any:
    last: Exception | None = None
    for url in urls:
        if time.monotonic() > deadline or http.is_down(url):
            continue
        try:
            payload = http.post_json(
                url,
                {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                ttl=15,
                timeout=12,
            )
        except HttpError as exc:
            last = exc
            continue
        if isinstance(payload, dict) and payload.get("error"):
            last = HttpError(str(payload["error"]))
            continue
        if isinstance(payload, dict) and "result" in payload:
            return payload["result"]
    if last:
        raise last
    raise HttpError("no public RPC responded")


def _pad(address: str) -> str:
    return "0x" + normalize_address("base", address).removeprefix("0x").rjust(64, "0")


def flows_from_logs(chain: str, token: str, decimals: int, logs: list[dict], prices: dict[str, float]) -> list[Flow]:
    flows: list[Flow] = []
    for log in logs:
        if not isinstance(log, dict) or log.get("removed"):
            continue
        topics = log.get("topics") or []
        if len(topics) < 3:
            continue
        src = "0x" + str(topics[1])[-40:]
        dst = "0x" + str(topics[2])[-40:]
        ts_raw = log.get("blockTimestamp") or log.get("blockTimestampMs")
        ts = parse_time(int(str(ts_raw), 16) if isinstance(ts_raw, str) and str(ts_raw).startswith("0x") else ts_raw)
        flow = _flow(
            chain=chain,
            token=token,
            raw=int(str(log.get("data") or "0x0"), 16),
            decimals=decimals,
            ts=ts,
            src=src,
            dst=dst,
            tx=str(log.get("transactionHash") or ""),
            log_index=int(str(log.get("logIndex") or "0x0"), 16) if str(log.get("logIndex") or "").startswith("0x") else log.get("logIndex") or 0,
            source="rpc",
            prices=prices,
        )
        if flow:
            flows.append(flow)
    return flows


def _rpc_token_logs(
    http: HttpClient,
    chain: str,
    holder: str,
    token: str,
    decimals: int,
    symbol: str,
    latest: int,
    span: int,
    deadline: float,
    cap: int,
    prices: dict[str, float],
) -> list[Flow]:
    """Read both directions, then keep the largest transfers plus the newest ones.

    A busy router can emit dozens of dust logs per block. Filling the cap with
    only the outgoing side, in block order, hides the transfers a person
    actually wants to see.
    """
    urls = list(CHAINS[chain]["rpcs"])
    padded = _pad(holder)
    per_direction = max(24, cap // 2)
    chosen: list[Flow] = []
    for topics in (
        [TRANSFER_TOPIC, padded],
        [TRANSFER_TOPIC, None, padded],
    ):
        if time.monotonic() > deadline:
            break
        raw: list[dict] = []
        cursor = latest
        target = max(0, latest - span)
        chunk = 1600 if chain != "arbitrum" else 5000
        while cursor > target and len(raw) < 180 and time.monotonic() < deadline:
            start = max(target, cursor - chunk)
            try:
                logs = _rpc(
                    http,
                    urls,
                    "eth_getLogs",
                    [{
                        "fromBlock": hex(start),
                        "toBlock": hex(cursor),
                        "address": token,
                        "topics": topics,
                    }],
                    deadline,
                )
            except HttpError:
                if chunk <= 400:
                    break
                chunk = max(400, chunk // 2)
                continue
            if isinstance(logs, list):
                raw.extend(item for item in logs if isinstance(item, dict))
            cursor = start - 1
            if len(raw) >= 80:
                break
        decoded = flows_from_logs(chain, symbol, decimals, raw, prices)
        by_size = sorted(decoded, key=lambda item: float(item.get("amount_value") or 0), reverse=True)
        by_time = sorted(decoded, key=lambda item: int(item.get("ts") or 0), reverse=True)
        picked: dict[str, Flow] = {}
        for item in by_size[:per_direction] + by_time[:12]:
            picked[str(item["id"])] = item
        chosen.extend(picked.values())
    return chosen


def fetch_evm(chain: str, address: str, http: HttpClient, prices: dict[str, float], *, deadline: float, lookback_hours: int, cap: int) -> tuple[list[Flow], list[str]]:
    warnings: list[str] = []
    meta = CHAINS[chain]
    blockscout = str(meta["blockscout"])
    items = _blockscout_pages(http, blockscout, address, deadline, cap)
    flows: list[Flow] = []
    if items is not None:
        flows.extend(flows_from_blockscout(chain, address, items, prices))
    else:
        warnings.append(f"{chain}: Blockscout was unavailable. Fell back to public RPC logs for major tokens.")
    need_rpc = items is None or len(flows) < 8
    if need_rpc and time.monotonic() < deadline:
        try:
            latest_hex = _rpc(http, list(meta["rpcs"]), "eth_blockNumber", [], deadline)
            latest = int(str(latest_hex), 16)
        except (HttpError, ValueError):
            warnings.append(f"{chain}: public RPC did not return a block number.")
            return _dedupe(flows)[:cap], warnings
        span = int((lookback_hours * 3600) / max(float(meta["block_seconds"]), 0.2))
        span = max(400, min(span, 20000 if chain != "arbitrum" else 80000))
        for symbol, token, decimals in TOKENS.get(chain, []):
            if time.monotonic() > deadline or len(flows) >= cap:
                break
            try:
                flows.extend(
                    _rpc_token_logs(
                        http, chain, address, token, decimals, symbol, latest, span, deadline, min(80, cap), prices
                    )
                )
            except HttpError as exc:
                warnings.append(f"{chain} {symbol}: {exc}")
        if items is None:
            warnings.append(
                f"{chain}: public RPC kept the largest recent transfers that fit the time budget, not every transfer in {lookback_hours}h."
            )
    return _dedupe(flows)[:cap], warnings


def fetch_near(address: str, http: HttpClient, prices: dict[str, float], *, deadline: float, cap: int) -> tuple[list[Flow], list[str]]:
    warnings: list[str] = []
    base = CHAINS["near"]["api"]
    flows: list[Flow] = []
    account = normalize_address("near", address)
    if time.monotonic() > deadline:
        return [], ["near: skipped, time budget spent"]
    try:
        ft = http.get_json(f"{base}/v1/account/{account}/ft-txns?per_page=25", ttl=40, timeout=10)
    except HttpError as exc:
        warnings.append(f"near: fungible-token history unavailable ({exc}).")
        ft = {}
    for item in (ft or {}).get("txns") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("cause") or "").upper() not in {"TRANSFER", "FT_TRANSFER"}:
            continue
        token = item.get("ft") if isinstance(item.get("ft"), dict) else {}
        decimals = int(to_decimal(token.get("decimals") or 0))
        raw = to_decimal(item.get("delta_amount"))
        if raw == 0:
            continue
        counterparty = str(item.get("involved_account_id") or "unknown.near")
        if raw > 0:
            src, dst = counterparty, account
        else:
            src, dst = account, counterparty
            raw = abs(raw)
        flow = _flow(
            chain="near",
            token=str(token.get("symbol") or "FT"),
            raw=raw,
            decimals=decimals,
            ts=parse_time(item.get("block_timestamp")),
            src=src,
            dst=dst,
            tx=str(item.get("transaction_hash") or ""),
            log_index=item.get("event_index") or 0,
            source="nearblocks",
            prices=prices,
        )
        if flow:
            flows.append(flow)
    if time.monotonic() < deadline:
        try:
            native = http.get_json(f"{base}/v1/account/{account}/txns?per_page=15", ttl=40, timeout=10)
        except HttpError as exc:
            warnings.append(f"near: native transfer history unavailable ({exc}).")
            native = {}
        for item in (native or {}).get("txns") or []:
            if not isinstance(item, dict):
                continue
            predecessor = str(item.get("predecessor_account_id") or "")
            receiver = str(item.get("receiver_account_id") or "")
            for action in item.get("actions") or []:
                if not isinstance(action, dict) or action.get("action") != "TRANSFER":
                    continue
                deposit = to_decimal(action.get("deposit"))
                if deposit <= 0:
                    continue
                flow = _flow(
                    chain="near",
                    token="NEAR",
                    raw=deposit,
                    decimals=24,
                    ts=parse_time(item.get("block_timestamp")),
                    src=predecessor,
                    dst=receiver,
                    tx=str(item.get("transaction_hash") or ""),
                    log_index="native",
                    source="nearblocks",
                    prices=prices,
                )
                if flow and (flow["src"] == account or flow["dst"] == account):
                    flows.append(flow)
    if not flows and not warnings:
        warnings.append(f"near: {account} has no fungible or native transfers in the public recent history.")
    return _dedupe(flows)[:cap], warnings


def fetch_solana(address: str, http: HttpClient, prices: dict[str, float], *, deadline: float, cap: int) -> tuple[list[Flow], list[str]]:
    warnings: list[str] = []
    rpc = CHAINS["solana"]["rpcs"][0]
    if time.monotonic() > deadline:
        return [], ["solana: skipped, time budget spent"]
    try:
        signatures = _rpc(
            http,
            [rpc],
            "getSignaturesForAddress",
            [address, {"limit": 8}],
            deadline,
        )
    except HttpError as exc:
        return [], [f"solana: public RPC unavailable ({exc})."]
    flows: list[Flow] = []
    if not isinstance(signatures, list):
        return [], ["solana: unexpected signature list."]
    for row in signatures[:8]:
        if time.monotonic() > deadline or len(flows) >= cap:
            break
        if not isinstance(row, dict) or row.get("err"):
            continue
        signature = str(row.get("signature") or "")
        try:
            tx = _rpc(
                http,
                [rpc],
                "getTransaction",
                [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
                deadline,
            )
        except HttpError:
            continue
        flows.extend(_solana_flows(address, signature, tx if isinstance(tx, dict) else {}, prices))
    if not flows:
        warnings.append("solana: no parsed transfers in the latest signatures.")
    return _dedupe(flows)[:cap], warnings


def _solana_flows(holder: str, signature: str, tx: dict, prices: dict[str, float]) -> list[Flow]:
    meta = tx.get("meta") if isinstance(tx.get("meta"), dict) else {}
    if meta.get("err"):
        return []
    message = ((tx.get("transaction") or {}).get("message") or {}) if isinstance(tx.get("transaction"), dict) else {}
    keys = []
    for key in message.get("accountKeys") or []:
        if isinstance(key, dict):
            keys.append(str(key.get("pubkey") or ""))
        else:
            keys.append(str(key))
    ts = parse_time(tx.get("blockTime"))
    flows: list[Flow] = []
    instructions: list[dict] = list(message.get("instructions") or [])
    for group in meta.get("innerInstructions") or []:
        if isinstance(group, dict):
            instructions.extend(group.get("instructions") or [])
    for index, instruction in enumerate(instructions):
        if not isinstance(instruction, dict):
            continue
        parsed = instruction.get("parsed")
        if not isinstance(parsed, dict):
            continue
        kind = str(parsed.get("type") or "")
        info = parsed.get("info") if isinstance(parsed.get("info"), dict) else {}
        if kind == "transfer" and "lamports" in info:
            flow = _flow(
                chain="solana",
                token="SOL",
                raw=info.get("lamports"),
                decimals=9,
                ts=ts,
                src=str(info.get("source") or ""),
                dst=str(info.get("destination") or ""),
                tx=signature,
                log_index=index,
                source="solana-rpc",
                prices=prices,
            )
        elif kind in {"transfer", "transferChecked"} and "tokenAmount" in info:
            token_amount = info.get("tokenAmount") if isinstance(info.get("tokenAmount"), dict) else {}
            decimals = int(to_decimal(token_amount.get("decimals") or info.get("decimals") or 0))
            raw = token_amount.get("amount")
            mint = str(info.get("mint") or "SPL")
            symbol = "USDC" if mint.startswith("EPjFW") else "SPL"
            flow = _flow(
                chain="solana",
                token=symbol,
                raw=raw,
                decimals=decimals,
                ts=ts,
                src=str(info.get("source") or info.get("authority") or ""),
                dst=str(info.get("destination") or ""),
                tx=signature,
                log_index=index,
                source="solana-rpc",
                prices=prices,
            )
        else:
            flow = None
        if flow and holder in {flow["src"], flow["dst"]}:
            flows.append(flow)
    if flows or not keys or holder not in keys:
        return flows
    pre = meta.get("preBalances") or []
    post = meta.get("postBalances") or []
    try:
        index = keys.index(holder)
        delta = int(post[index]) - int(pre[index])
    except (ValueError, IndexError, TypeError):
        return flows
    if delta == 0:
        return flows
    counterparty = ""
    for other, before, after in zip(keys, pre, post):
        if other == holder:
            continue
        try:
            change = int(after) - int(before)
        except (TypeError, ValueError):
            continue
        if delta > 0 and change < 0:
            counterparty = other
            break
        if delta < 0 and change > 0:
            counterparty = other
            break
    if not counterparty:
        return flows
    src, dst = (counterparty, holder) if delta > 0 else (holder, counterparty)
    flow = _flow(
        chain="solana",
        token="SOL",
        raw=abs(delta),
        decimals=9,
        ts=ts,
        src=src,
        dst=dst,
        tx=signature,
        log_index="balance",
        source="solana-rpc",
        prices=prices,
    )
    return [flow] if flow else []


def fetch_watch(watch: dict, http: HttpClient, prices: dict[str, float], *, deadline: float, lookback_hours: int, cap: int) -> tuple[list[Flow], list[str]]:
    chain = watch["chain"]
    address = watch["address"]
    if chain in {"ethereum", "base", "arbitrum", "optimism"}:
        return fetch_evm(chain, address, http, prices, deadline=deadline, lookback_hours=lookback_hours, cap=cap)
    if chain == "near":
        return fetch_near(address, http, prices, deadline=deadline, cap=cap)
    if chain == "solana":
        return fetch_solana(address, http, prices, deadline=deadline, cap=cap)
    return [], [f"unsupported chain {chain}"]


def _dedupe(flows: list[Flow]) -> list[Flow]:
    seen: set[str] = set()
    ordered: list[Flow] = []
    for flow in sorted(flows, key=lambda item: int(item.get("ts") or 0), reverse=True):
        key = str(flow.get("id"))
        if key in seen:
            continue
        seen.add(key)
        ordered.append(flow)
    return ordered


def symbols_in(flows: list[Flow]) -> set[str]:
    return {str(flow.get("token") or "") for flow in flows if flow.get("token")}
