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


def _rank_key(row: dict[str, Any]) -> tuple[float, float]:
    """Priced transfers rank by USD. Unpriced ones rank by token amount, below any priced transfer."""
    amount = float(row.get("amount_value") or 0)
    usd = row.get("usd")
    if usd is None:
        return (0.0, amount)
    return (1.0, float(usd))


def largest_by_direction(flows: list[dict[str, Any]], direction: str) -> dict[str, Any] | None:
    """Largest transfer of one direction.

    Direction is assigned once, before this runs: ``in`` means the destination
    is a watched address and the source is not. ``out`` is the reverse.
    A transfer between two watched addresses is ``internal`` and is neither.
    """
    rows = [flow for flow in flows if flow.get("direction") == direction]
    if not rows:
        return None
    return max(rows, key=_rank_key)


def inflow_headline(largest_in: dict[str, Any] | None, count: int) -> str:
    """The one sentence the pane, the summary tool, and the CLI all show."""
    if not largest_in:
        return f"No inflow in the scanned window. {count} transfers."
    return f"Largest inflow {_money(largest_in)} · {count} transfers in the scanned window."


def summarize(flows: list[dict[str, Any]], watches: list[dict[str, Any]], *, requested_hours: int, warnings: list[str]) -> dict[str, Any]:
    largest_in = largest_by_direction(flows, "in")
    largest_out = largest_by_direction(flows, "out")
    inbound = [flow for flow in flows if flow.get("direction") == "in"]
    outbound = [flow for flow in flows if flow.get("direction") == "out"]
    head = inflow_headline(largest_in, len(flows))
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
    lines.append(head)
    if largest_in:
        lines.append(
            f"That inflow moved from {_party(largest_in, 'src')} "
            f"to {_party(largest_in, 'dst')} on {largest_in['chain']} at {format_time(largest_in.get('ts'))}."
        )
        lines.append(f"Inflow explorer: {largest_in.get('explorer')}")
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
        "headline": head,
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
