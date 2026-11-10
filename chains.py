"""Chain metadata and address checks. Public explorers only."""

from __future__ import annotations

import re

EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
NEAR_NAMED_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,57}\.(?:near|tg)$")
NEAR_IMPLICIT_RE = re.compile(r"^[0-9a-f]{64}$")
SOL_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

CHAIN_ALIASES = {
    "base": "base",
    "ethereum": "ethereum",
    "eth": "ethereum",
    "mainnet": "ethereum",
    "arbitrum": "arbitrum",
    "arb": "arbitrum",
    "optimism": "optimism",
    "op": "optimism",
    "near": "near",
    "solana": "solana",
    "sol": "solana",
}

EVM_CHAINS = {"ethereum", "base", "arbitrum", "optimism"}

# Major tokens used when an explorer is down and Flowlight falls back to public logs.
TOKENS: dict[str, list[tuple[str, str, int]]] = {
    "base": [
        ("USDC", "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", 6),
        ("WETH", "0x4200000000000000000000000000000000000006", 18),
        ("USDbC", "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca", 6),
        ("AERO", "0x940181a94a35a4569e4529a3cdfb74e38fd98631", 18),
    ],
    "ethereum": [
        ("USDC", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 6),
        ("USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7", 6),
        ("WETH", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 18),
        ("DAI", "0x6b175474e89094c44da98b954eedeac495271d0f", 18),
    ],
    "arbitrum": [
        ("USDC", "0xaf88d065e77c8cc2239327c5edb3a432268e5831", 6),
        ("USDT", "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9", 6),
        ("WETH", "0x82af49447d8a07e3bd95bd0d56f35241523fbab1", 18),
    ],
    "optimism": [
        ("USDC", "0x0b2c639c533813f4aa9d7837caf62653d097ff85", 6),
        ("USDT", "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58", 6),
        ("WETH", "0x4200000000000000000000000000000000000006", 18),
    ],
}

CHAINS: dict[str, dict] = {
    "ethereum": {
        "kind": "evm",
        "native": "ETH",
        "block_seconds": 12,
        "blockscout": "https://eth.blockscout.com",
        "rpcs": [
            "https://ethereum.publicnode.com",
            "https://eth.drpc.org",
            "https://rpc.mevblocker.io",
        ],
    },
    "base": {
        "kind": "evm",
        "native": "ETH",
        "block_seconds": 2,
        "blockscout": "https://base.blockscout.com",
        "rpcs": [
            "https://base-rpc.publicnode.com",
            "https://mainnet.base.org",
            "https://base.drpc.org",
            "https://base.meowrpc.com",
        ],
    },
    "arbitrum": {
        "kind": "evm",
        "native": "ETH",
        "block_seconds": 0.25,
        "blockscout": "https://arbitrum.blockscout.com",
        "rpcs": [
            "https://arbitrum.publicnode.com",
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.drpc.org",
        ],
    },
    "optimism": {
        "kind": "evm",
        "native": "ETH",
        "block_seconds": 2,
        "blockscout": "https://optimism.blockscout.com",
        "rpcs": [
            "https://optimism.publicnode.com",
            "https://mainnet.optimism.io",
            "https://optimism.drpc.org",
        ],
    },
    "near": {
        "kind": "near",
        "native": "NEAR",
        "api": "https://api.nearblocks.io",
    },
    "solana": {
        "kind": "solana",
        "native": "SOL",
        "rpcs": ["https://api.mainnet-beta.solana.com"],
    },
}

KNOWN_LABELS = {
    ("base", "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"): "USDC",
    ("base", "0x4200000000000000000000000000000000000006"): "WETH",
    ("base", "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca"): "USDbC",
    ("base", "0x940181a94a35a4569e4529a3cdfb74e38fd98631"): "AERO",
    ("ethereum", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"): "USDC",
    ("ethereum", "0xdac17f958d2ee523a2206206994597c13d831ec7"): "USDT",
    ("ethereum", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"): "WETH",
    ("near", "wrap.near"): "wNEAR",
    ("near", "intents.near"): "NEAR Intents",
    ("near", "purefile1686.near"): "purefile1686.near",
}

COINGECKO_IDS = {
    "ETH": "ethereum",
    "NEAR": "near",
    "SOL": "solana",
    "BTC": "bitcoin",
    "USDC": "usd-coin",
    "USDT": "tether",
    "DAI": "dai",
}


def canonical_chain(value: str | None) -> str | None:
    if not value:
        return None
    return CHAIN_ALIASES.get(value.strip().lower())


def is_evm_address(value: str) -> bool:
    return bool(EVM_RE.match(value or ""))


def is_near_account(value: str) -> bool:
    text = (value or "").strip().lower()
    return bool(NEAR_NAMED_RE.match(text) or NEAR_IMPLICIT_RE.match(text))


def is_solana_address(value: str) -> bool:
    return bool(SOL_RE.match(value or ""))


def normalize_address(chain: str, address: str) -> str:
    text = (address or "").strip()
    if chain in EVM_CHAINS:
        return text.lower()
    if chain == "near":
        return text.lower()
    return text


def node_id(chain: str, address: str) -> str:
    return f"{chain}:{normalize_address(chain, address)}"


def known_label(chain: str, address: str) -> str | None:
    return KNOWN_LABELS.get((chain, normalize_address(chain, address)))


def explorer_tx(chain: str, tx_hash: str) -> str:
    if chain == "near":
        return f"https://nearblocks.io/txns/{tx_hash}"
    if chain == "solana":
        return f"https://solscan.io/tx/{tx_hash}"
    host = {
        "ethereum": "https://eth.blockscout.com",
        "base": "https://base.blockscout.com",
        "arbitrum": "https://arbitrum.blockscout.com",
        "optimism": "https://optimism.blockscout.com",
    }.get(chain, "https://blockscout.com")
    return f"{host}/tx/{tx_hash}"


def explorer_address(chain: str, address: str) -> str:
    if chain == "near":
        return f"https://nearblocks.io/address/{address}"
    if chain == "solana":
        return f"https://solscan.io/account/{address}"
    host = {
        "ethereum": "https://eth.blockscout.com",
        "base": "https://base.blockscout.com",
        "arbitrum": "https://arbitrum.blockscout.com",
        "optimism": "https://optimism.blockscout.com",
    }.get(chain, "https://blockscout.com")
    return f"{host}/address/{address}"
