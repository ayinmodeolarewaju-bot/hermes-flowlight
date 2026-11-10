"""Slash command and ``hermes flowlight`` CLI."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .runtime import make_deps
from .service import flow_list, list_accounts, summary_only, unwatch_accounts, watch_accounts


def parse_slash(raw: str) -> tuple[str, dict[str, Any]] | tuple[None, str]:
    parts = (raw or "").strip().split()
    if not parts or parts[0] in {"help", "-h", "--help"}:
        return None, _usage()
    action = parts[0].lower()
    rest = parts[1:]
    if action == "list":
        return "list", {}
    if action == "demo":
        return "demo", {"demo": True}
    if action == "summary":
        return "summary", {}
    if action == "flows":
        return "flows", {}
    if action == "watch":
        if not rest:
            return None, _usage()
        return "watch", {"text": " ".join(rest)}
    if action == "unwatch":
        if not rest:
            return None, _usage()
        return "unwatch", {"text": " ".join(rest)}
    if action == "serve":
        return "serve", {"port": int(rest[0]) if rest else 8787}
    return None, _usage()


def _usage() -> str:
    return (
        "Usage:\n"
        "/flowlight watch purefile1686.near and 0xADDRESS on Base\n"
        "/flowlight unwatch 0xADDRESS on Base\n"
        "/flowlight flows\n"
        "/flowlight summary\n"
        "/flowlight list\n"
        "/flowlight demo\n"
        "Read-only. Flowlight never asks for a key and never sends a transaction.\n"
        "The picture is `hermes flowlight serve` on a loopback page."
    )


def slash_command(raw_args: str, **kwargs: Any) -> str:
    parsed = parse_slash(raw_args)
    if parsed[0] is None:
        return str(parsed[1])
    action, args = parsed
    if action == "serve":
        return "Start the picture from a terminal with: hermes flowlight serve"
    deps = kwargs.get("_deps") or make_deps(kwargs.get("ctx"))
    if action == "watch":
        result = watch_accounts(args, deps)
    elif action == "unwatch":
        result = unwatch_accounts(args, deps)
    elif action == "flows":
        result = flow_list(args, deps)
    elif action == "demo":
        result = summary_only(args, deps)
    elif action == "summary":
        result = summary_only(args, deps)
    else:
        result = list_accounts(deps)
    summary = (result.get("summary") or {}).get("text")
    if summary:
        return str(summary)
    return json.dumps(result, indent=2, default=str)


def setup_cli(subparser: argparse.ArgumentParser) -> None:
    commands = subparser.add_subparsers(dest="flowlight_action")
    watch = commands.add_parser("watch", help="Watch a public address")
    watch.add_argument("target", nargs="*", help="Address or phrase")
    watch.add_argument("--chain", default=None)
    watch.add_argument("--label", default=None)
    watch.add_argument("--demo", action="store_true")
    unwatch = commands.add_parser("unwatch", help="Stop watching an address")
    unwatch.add_argument("target", nargs="*")
    unwatch.add_argument("--chain", default=None)
    commands.add_parser("list", help="Show watched addresses")
    flows = commands.add_parser("flows", help="List recent transfers")
    flows.add_argument("--window-hours", type=int, default=None)
    flows.add_argument("--limit", type=int, default=20)
    flows.add_argument("--demo", action="store_true")
    flows.add_argument("--json", action="store_true")
    summary = commands.add_parser("summary", help="Narrate the largest flows")
    summary.add_argument("--window-hours", type=int, default=None)
    summary.add_argument("--demo", action="store_true")
    summary.add_argument("--json", action="store_true")
    commands.add_parser("demo", help="Print the labeled offline fixture summary")
    serve = commands.add_parser("serve", help="Open the flow picture on loopback")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--demo", action="store_true", help="Open on the labeled fixture until the page asks for live data")
    subparser.set_defaults(func=handle_cli)


def _print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, default=str))
        return
    text = (result.get("summary") or {}).get("text")
    if text:
        print(text)
        return
    print(json.dumps(result, indent=2, default=str))


def handle_cli(args: argparse.Namespace) -> None:
    action = getattr(args, "flowlight_action", None)
    if action == "serve":
        from .serve import serve

        serve(port=args.port, demo=bool(args.demo))
        return
    deps = make_deps()
    if action == "watch":
        text = " ".join(args.target or [])
        result = watch_accounts(
            {"text": text, "chain": args.chain, "label": args.label, "demo": args.demo},
            deps,
        )
        _print_result(result, False)
        return
    if action == "unwatch":
        result = unwatch_accounts({"text": " ".join(args.target or []), "chain": args.chain}, deps)
        _print_result(result, False)
        return
    if action == "flows":
        result = flow_list(
            {"window_hours": args.window_hours, "limit": args.limit, "demo": args.demo},
            deps,
        )
        _print_result(result, args.json)
        return
    if action == "summary":
        result = summary_only({"window_hours": args.window_hours, "demo": args.demo}, deps)
        _print_result(result, args.json)
        return
    if action == "demo":
        result = summary_only({"demo": True}, deps)
        _print_result(result, False)
        return
    if action == "list":
        _print_result(list_accounts(deps), False)
        return
    print(_usage())
