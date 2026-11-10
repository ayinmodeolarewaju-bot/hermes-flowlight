---
name: watch
description: Watch public wallet addresses and narrate on-chain money flows with Flowlight. Use when the user wants to watch a NEAR or EVM address, see recent transfers, summarize inflows and outflows, or check Intents Pay invoices.
---

# Flowlight

Use the Flowlight tools for on-chain watches. Numbers, addresses, and explorer links come from the tool result. Refuse any seed phrase, recovery phrase, or signing key. This plugin cannot sign or send a transaction.

## Tool order

1. `flowlight_watch` with the user's phrase. Example text: `purefile1686.near and 0x… on Base`.
2. Tell the user the `summary.text` that comes back. Name the window it actually scanned.
3. `flowlight_summary` when they ask for the largest inflow or outflow.
4. `flowlight_flows` when they want individual transfers.
5. `flowlight_list` and `flowlight_unwatch` to show or drop watches.
6. `flowlight_invoices` when they ask about an Intents Pay invoice. If the note says no Intents Pay invoices were found, say that and do not invent one. A `fixture: true` invoice is the demo fixture, not a live invoice.

`/flowlight` is the same read path. `hermes flowlight serve` opens the animated picture on loopback.

## What to say

- Quote amounts, tokens, and the explorer URL from the tool. Do not fill gaps from memory.
- If `demo` is true, say it is the labeled demo fixture and not live chain data.
- If a warning says the window is shorter than 24 hours, say that. Busy addresses are capped at the recent public slice.
- A quiet account is a real result. Say that no transfers came back. Do not invent a flow to fill the picture.
