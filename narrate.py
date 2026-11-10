"""Plain-language summary of a flow set. Numbers come only from the flows passed in."""

from __future__ import annotations

from typing import Any

from .money import format_time, format_usd, short_address


def _party(flow: dict[str, Any], side: str) -> str:
    label = flow.get(f"{side}_label")
    address = str(flow.get(side) or "")
    if label and label != address:
        return f"{label} ({short_address(address)})"
    return short_address(address)


def _money(flow: dict[str, Any]) -> str:
    usd = format_usd(flow.get("usd"))
    base = f"{flow.get('amount')} {flow.get('token')}"
    return f"{base} ({usd})" if usd else base


def summarize(flows: list[dict[str, Any]], watches: list[dict[str, Any]], *, requested_hours: int, warnings: list[str]) -> dict[str, Any]:
    inbound = [flow for flow in flows if flow.get("direction") == "in"]
    outbound = [flow for flow in flows if flow.get("direction") == "out"]

    def rank(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        priced = [row for row in rows if row.get("usd") is not None]
        pool = priced or rows
        if not pool:
            return None
        return max(pool, key=lambda row: float(row.get("usd") if row.get("usd") is not None else row.get("amount_value") or 0))

    largest_in = rank(inbound)
    largest_out = rank(outbound)
    in_usd = sum(float(row["usd"]) for row in inbound if row.get("usd") is not None)
    out_usd = sum(float(row["usd"]) for row in outbound if row.get("usd") is not None)
    stamps = [int(row["ts"]) for row in flows if row.get("ts")]
    start = min(stamps) if stamps else None
    end = max(stamps) if stamps else None
    span_hours = ((end - start) / 3600) if start and end else 0
    complete = bool(stamps) and span_hours >= requested_hours * 0.9
    names = ", ".join(
        f"{item.get('label') or short_address(item['address'])} on {item['chain']}" for item in watches
    ) or "nobody"
    lines = [f"Watched {names}."]
    if not flows:
        lines.append("No transfers came back for this window.")
    else:
        coverage = (
            f"The scanned window runs {format_time(start)} to {format_time(end)} "
            f"({len(flows)} transfers)."
        )
        if not complete:
            coverage += (
                f" That is shorter than the requested {requested_hours}h lookback: "
                "public endpoints return the recent slice, and busy addresses hit the read cap first."
            )
        lines.append(coverage)
    if largest_in:
        lines.append(
            f"Largest inflow was {_money(largest_in)} from {_party(largest_in, 'src')} "
            f"to {_party(largest_in, 'dst')} on {largest_in['chain']} at {format_time(largest_in.get('ts'))}."
        )
        lines.append(f"Inflow explorer: {largest_in.get('explorer')}")
    else:
        lines.append("No inflow in the scanned window.")
    if largest_out:
        lines.append(
            f"Largest outflow was {_money(largest_out)} from {_party(largest_out, 'src')} "
            f"to {_party(largest_out, 'dst')} on {largest_out['chain']} at {format_time(largest_out.get('ts'))}."
        )
    else:
        lines.append("No outflow in the scanned window.")
    if in_usd or out_usd:
        net = in_usd - out_usd
        lines.append(
            f"Priced volume: {format_usd(in_usd)} in, {format_usd(out_usd)} out, net {format_usd(net)}."
        )
    quiet = []
    for watch in watches:
        touched = any(flow.get("chain") == watch["chain"] and watch["address"] in {flow.get("src"), flow.get("dst")} for flow in flows)
        if not touched:
            quiet.append(watch.get("label") or short_address(watch["address"]))
    if quiet:
        lines.append("No transfers in this window for " + ", ".join(quiet) + ".")
    if warnings:
        lines.append("Notes: " + " ".join(warnings))
    return {
        "text": " ".join(lines),
        "largest_inflow": largest_in,
        "largest_outflow": largest_out,
        "in_usd": round(in_usd, 2),
        "out_usd": round(out_usd, 2),
        "net_usd": round(in_usd - out_usd, 2),
        "count": len(flows),
        "window_start": start,
        "window_end": end,
        "requested_hours": requested_hours,
        "complete": complete,
        "label": "LIVE",
    }
