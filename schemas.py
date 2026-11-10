"""Tool schemas shown to the Hermes model."""

from __future__ import annotations

_SAFETY = (
    "Read-only. Never ask for a seed phrase, private key, or signing key. "
    "This tool does not sign or send transactions. "
    "Pass demo=true only when the user wants the labeled offline fixture. "
    "Live reads use public NEAR, Blockscout, and RPC endpoints and can be partial on busy addresses."
)

FLOWLIGHT_WATCH = {
    "name": "flowlight_watch",
    "description": (
        "Start watching one or more public wallets so Flowlight can draw their transfers. "
        "Use when the user says to watch an address, for example purefile1686.near and an 0x address on Base. "
        "NEAR accounts and 0x addresses can share one text string. EVM addresses need a chain "
        "(base, ethereum, arbitrum, optimism), written as 'on Base' or passed as chain. "
        + _SAFETY
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Natural phrase such as 'purefile1686.near and 0xabc… on Base'.",
            },
            "address": {
                "type": "string",
                "description": "A single public address. Use text instead when several addresses are named together.",
            },
            "chain": {
                "type": "string",
                "description": "base, ethereum, arbitrum, optimism, near, or solana. Required for a bare 0x address.",
            },
            "label": {
                "type": "string",
                "description": "Optional short name shown on the node.",
            },
            "demo": {
                "type": "boolean",
                "description": "When true, return the labeled demo fixture instead of live transfers.",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
}

FLOWLIGHT_UNWATCH = {
    "name": "flowlight_unwatch",
    "description": "Stop watching a public address. Use when the user asks to unwatch or remove an address from Flowlight. " + _SAFETY,
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Address or phrase naming what to stop watching."},
            "address": {"type": "string", "description": "Public address to remove."},
            "chain": {"type": "string", "description": "Chain for a bare 0x address."},
        },
        "required": [],
        "additionalProperties": False,
    },
}

FLOWLIGHT_FLOWS = {
    "name": "flowlight_flows",
    "description": (
        "List recent transfers for the watched addresses, with token, amount, USD when priced, "
        "direction, timestamp, and an explorer link. Use this when the user wants the transfers themselves. "
        + _SAFETY
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "window_hours": {"type": "integer", "description": "Requested lookback in hours. Default is the plugin setting, usually 24."},
            "limit": {"type": "integer", "description": "Maximum rows in the list. Default 40."},
            "chain": {"type": "string", "description": "Optional chain filter."},
            "address": {"type": "string", "description": "Optional address filter. Matches either side of a transfer."},
            "demo": {"type": "boolean", "description": "Return the labeled demo fixture."},
            "live": {"type": "boolean", "description": "Force a live read even if demo mode is configured."},
        },
        "required": [],
        "additionalProperties": False,
    },
}

FLOWLIGHT_SUMMARY = {
    "name": "flowlight_summary",
    "description": (
        "Summarize watched flows: largest inflow, largest outflow, priced in and out totals, "
        "and the time window actually scanned. Use this when the user asks what the biggest flow was "
        "or wants a narration. Quote the summary text and the explorer link. Do not invent a transfer "
        "that is not in the result. " + _SAFETY
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "window_hours": {"type": "integer", "description": "Requested lookback in hours."},
            "demo": {"type": "boolean", "description": "Summarize the labeled demo fixture."},
            "live": {"type": "boolean", "description": "Force a live read even if demo mode is configured."},
        },
        "required": [],
        "additionalProperties": False,
    },
}

FLOWLIGHT_LIST = {
    "name": "flowlight_list",
    "description": "List the addresses Flowlight is watching. Use this before adding a duplicate or when the user asks what is watched. " + _SAFETY,
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
}

TOOL_SCHEMAS = {
    "flowlight_watch": FLOWLIGHT_WATCH,
    "flowlight_unwatch": FLOWLIGHT_UNWATCH,
    "flowlight_flows": FLOWLIGHT_FLOWS,
    "flowlight_summary": FLOWLIGHT_SUMMARY,
    "flowlight_list": FLOWLIGHT_LIST,
}
