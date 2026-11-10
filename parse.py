"""Turn a chat phrase into watch targets. Rejects anything that looks like a key."""

from __future__ import annotations

import re
from typing import Any

from .chains import canonical_chain, is_evm_address, is_near_account, is_solana_address, normalize_address

_SECRET_WORDS = re.compile(
    r"\b(seed phrase|recovery phrase|mnemonic|private key|secret key|signing key)\b",
    re.I,
)
_ON_CHAIN = re.compile(
    r"\bon\s+(base|ethereum|eth|mainnet|arbitrum|arb|optimism|op|near|solana|sol)\b",
    re.I,
)
_EVM = re.compile(r"(?<![\w])0x[a-fA-F0-9]{40}(?![\w])")
_NEAR = re.compile(r"(?<![\w.])[a-z0-9][a-z0-9_\-]{0,57}\.(?:near|tg)(?![\w.])", re.I)
_SOL = re.compile(r"(?<![\w])[1-9A-HJ-NP-Za-km-z]{32,44}(?![\w])")
_SPLIT = re.compile(r"\s+(?:and|&)\s+|[,;\n]+", re.I)


class InputError(ValueError):
    pass


def secret_material_error(text: str) -> str | None:
    """Refuse seed phrases and key material. Addresses are public and allowed."""
    if not text or not text.strip():
        return None
    if _SECRET_WORDS.search(text):
        return "Flowlight is read-only and does not accept seed phrases or signing keys."
    words = [part for part in re.split(r"\s+", text.strip()) if part]
    if len(words) >= 12 and all(re.fullmatch(r"[a-zA-Z]+", word) for word in words):
        return "Flowlight is read-only and does not accept seed phrases or signing keys."
    return None


def _segment_chain(segment: str) -> str | None:
    match = _ON_CHAIN.search(segment)
    if match:
        return canonical_chain(match.group(1))
    return None


def _targets_in_segment(segment: str, forced_chain: str | None) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    chain_hint = forced_chain or _segment_chain(segment)
    for match in _NEAR.finditer(segment):
        account = match.group(0).lower()
        found.append({"address": account, "chain": "near"})
    for match in _EVM.finditer(segment):
        found.append({"address": match.group(0), "chain": chain_hint or ""})
    if chain_hint == "solana" or (forced_chain == "solana"):
        for match in _SOL.finditer(segment):
            token = match.group(0)
            if is_solana_address(token) and not is_near_account(token):
                found.append({"address": token, "chain": "solana"})
    return found


def parse_watch_text(text: str, chain: str | None = None) -> list[dict[str, str]]:
    """Parse ``purefile1686.near and 0x… on Base`` into address/chain pairs."""
    secret = secret_material_error(text)
    if secret:
        raise InputError(secret)
    forced = canonical_chain(chain) if chain else None
    if chain and not forced:
        raise InputError(f"Unknown chain {chain!r}. Use base, ethereum, arbitrum, optimism, near, or solana.")
    segments = [part.strip() for part in _SPLIT.split(text or "") if part.strip()]
    if not segments and (text or "").strip():
        segments = [text.strip()]
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for segment in segments:
        for item in _targets_in_segment(segment, forced):
            item_chain = item["chain"] or (forced or "")
            if not item_chain:
                if is_near_account(item["address"]):
                    item_chain = "near"
                else:
                    raise InputError(
                        f"Chain required for {item['address']}. Say which chain, for example 'on Base'."
                    )
            address = normalize_address(item_chain, item["address"])
            key = (item_chain, address)
            if key in seen:
                continue
            seen.add(key)
            found.append({"address": address, "chain": item_chain})
    if not found:
        raise InputError("No public address found. Example: purefile1686.near and 0xabc… on Base.")
    return found


def coerce_watch_args(args: dict[str, Any]) -> list[dict[str, str]]:
    text = str(args.get("text") or args.get("query") or "").strip()
    address = str(args.get("address") or "").strip()
    chain = args.get("chain")
    blob = text or address
    secret = secret_material_error(blob) or secret_material_error(str(args.get("label") or ""))
    if secret:
        raise InputError(secret)
    if text:
        return parse_watch_text(text, str(chain) if chain else None)
    if address:
        return parse_watch_text(address, str(chain) if chain else None)
    raise InputError("Pass address and chain, or text like 'purefile1686.near and 0x… on Base'.")
