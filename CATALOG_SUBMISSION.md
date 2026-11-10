# Catalog submission (do not open this PR from automation)

Prepared for the Hermes Agent Plugin Hackathon. This file is the catalog change. It is **not** opened here. The plugin repository is public. The catalog pull request on `NousResearch/hermes-agent` is updated by the owner, not by this branch.

## Where the entry goes

- Repository: `https://github.com/NousResearch/hermes-agent`
- Path: `plugin-catalog/flowlight.yaml`
- One file. No other edits.
- Base branch: `main`
- The submitter must be the owner of `ayinmodeolarewaju-bot/hermes-flowlight` (catalog rule 5).

## Pin

Pin this commit. It is the plugin tree (code, tests, README, screenshots, dashboard bundle, demo). A later commit on this branch only records the hash in this file.

`8d6aacb1babc9136316f7b1777d436027771676b`

```yaml
name: flowlight
repo: https://github.com/ayinmodeolarewaju-bot/hermes-flowlight
sha: 8d6aacb1babc9136316f7b1777d436027771676b
description: >
  Watch public wallets and draw live on-chain money flows as glowing arcs.
  Read-only. Uses public NEAR, Blockscout, and RPC endpoints. When Intents
  Pay is installed, reads its invoice ledger and may GET 1-Click /v0/status.
  Never signs or sends transactions and never handles keys.
maintainer: ayinmodeolarewaju-bot
tier: community
category: tools
requires_hermes: ">=0.22.0"
version: "1.1.0"
title: Flowlight
docs_url: https://github.com/ayinmodeolarewaju-bot/hermes-flowlight
image: https://raw.githubusercontent.com/ayinmodeolarewaju-bot/hermes-flowlight/8d6aacb1babc9136316f7b1777d436027771676b/docs/screenshots/banner.png
screenshots:
  - https://raw.githubusercontent.com/ayinmodeolarewaju-bot/hermes-flowlight/8d6aacb1babc9136316f7b1777d436027771676b/docs/screenshots/live-flows.png
  - https://raw.githubusercontent.com/ayinmodeolarewaju-bot/hermes-flowlight/8d6aacb1babc9136316f7b1777d436027771676b/docs/screenshots/arc-detail.png
  - https://raw.githubusercontent.com/ayinmodeolarewaju-bot/hermes-flowlight/8d6aacb1babc9136316f7b1777d436027771676b/docs/screenshots/invoice-pending.png
  - https://raw.githubusercontent.com/ayinmodeolarewaju-bot/hermes-flowlight/8d6aacb1babc9136316f7b1777d436027771676b/docs/screenshots/invoice-paid.png
  - https://raw.githubusercontent.com/ayinmodeolarewaju-bot/hermes-flowlight/8d6aacb1babc9136316f7b1777d436027771676b/docs/screenshots/demo-fixture.png
readme: true
platforms: []
known_issues:
  - "Base and Arbitrum Blockscout often answer HTTP 403 from datacenter networks. Flowlight falls back to public JSON-RPC logs for major tokens and says so."
  - "A busy address is summarized over the largest recent slice that fits the time budget, not every transfer in the requested 24h."
  - "purefile1686.near had no fungible or native transfers in the public recent history during the 10 Nov 2026 live run. The node still draws."
  - "Intents Pay is optional. If its ledger is missing, Flowlight reports that no Intents Pay invoices were found and keeps working."
  - "The gold paid burst in the demo fixture is labeled DEMO FIXTURE. It is not a live settlement."
capabilities:
  provides_tools:
    - flowlight_watch
    - flowlight_unwatch
    - flowlight_flows
    - flowlight_summary
    - flowlight_list
    - flowlight_invoices
  provides_hooks: []
  provides_middleware: []
  requires_env: []
```

`subdir` is omitted because `plugin.yaml` is at the repository root.

Suggested PR title: `catalog: add flowlight`

## PR description to paste

Flowlight watches public wallets and draws their transfers as glowing arcs. Hermes can name the largest inflow and outflow from the same read. When Intents Pay is installed, Flowlight reads that invoice ledger and draws a pending ring or a paid gold arc. It does not create quotes or move funds.

Surfaces:

- Six tools: watch, unwatch, flows, summary, list, invoices
- `/flowlight` slash command, including `/flowlight invoices`
- `hermes flowlight` CLI, including `hermes flowlight invoices` and `hermes flowlight serve`
- Bundled skill `flowlight:watch`
- Desktop pane, full page, sidebar row, status chip (`desktop/plugin.js`)
- Dashboard tab and API (`dashboard/`)

Rule 13 disclosure:

- Outbound HTTPS only, to public endpoints: `api.nearblocks.io`, Blockscout instances for Ethereum, Base, Arbitrum, and Optimism, public EVM RPCs (publicnode, `mainnet.base.org`, drpc, meowrpc, and the Arbitrum and Optimism public RPCs), `api.mainnet-beta.solana.com`, `api.coingecko.com` for USD prices, and `GET https://1click.chaindefuser.com/v0/status` when an Intents Pay invoice has a deposit address. No API key.
- Writes a watch list and a short flow cache under the profile plugin-data directory. Reads the Intents Pay ledger at `plugin-data/intents-pay/ledger.json` when that file exists. Does not write that ledger. No telemetry, no shell commands, no credential-file reads.
- `hermes flowlight serve` is a loopback HTTP server the user starts on purpose. It binds to 127.0.0.1.
- Read-only. The plugin refuses input that looks like a seed phrase or signing key. It never builds, signs, or broadcasts a transaction, and it never asks 1-Click for a quote.
- If a live read fails, the picture keeps the last good slice or shows a warning. It does not silently swap in the demo fixture. Demo mode is explicit and labeled.

Screenshots are the files named in `screenshots:` (10 Nov 2026). `invoice-pending.png` is the live dry invoice `IP-20261110-82B7` (25 USDC to `purefile1686.near`, no deposit). `invoice-paid.png` is the labeled fixture burst. The animation capture is `docs/demo/flowlight-demo-v3.mp4` in the pinned tree.

Local check already run on Hermes Agent v0.23.0:

```text
hermes plugins validate <plugin> --install-deps   # ok, security scan safe
hermes plugins doctor <plugin> --ci               # 6 tools
```

## What has to happen before the catalog PR is eligible

1. `https://github.com/ayinmodeolarewaju-bot/hermes-flowlight` is public, so catalog CI can clone the pinned commit.
2. Confirm the pinned commit is the one named `sha:` above, and that this tree contains `plugin.yaml`, `__init__.py`, `desktop/plugin.js`, and the screenshots.
3. Open or update the PR yourself (owner account) against `NousResearch/hermes-agent`, changing only `plugin-catalog/flowlight.yaml`. Do not set `tier` to `official` or `verified`.
4. Wait until the catalog CI job is green. It clones this repo at `sha` and runs `hermes plugins validate --install-deps`.
5. Post a demo video under 90 seconds on X, tag `@NousResearch`, and show the plugin working. Shot list: `DEMO_SCRIPT.md`.
6. Submit the catalog PR link and the X link at `https://form.typeform.com/to/FwJLvOln`. Deadline: 11 Nov 2026, 5 PM EST.

Hackathon entry is the plugin. This repository's own pull request only lands the source. It is not the catalog PR.
