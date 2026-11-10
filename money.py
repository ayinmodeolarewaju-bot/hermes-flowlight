"""Amount formatting. No chain calls."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone


def to_decimal(value: object) -> Decimal:
    if value is None or isinstance(value, bool):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "nan"}:
        return Decimal(0)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal(0)


def from_base_units(raw: object, decimals: int) -> Decimal:
    amount = to_decimal(raw)
    places = max(0, int(decimals or 0))
    if places == 0:
        return amount
    return amount / (Decimal(10) ** places)


def format_amount(amount: Decimal) -> str:
    value = to_decimal(amount)
    absolute = abs(value)
    if absolute == 0:
        return "0"
    if absolute >= 1000:
        quantum = Decimal("0.01")
    elif absolute >= 1:
        quantum = Decimal("0.0001")
    elif absolute >= Decimal("0.0001"):
        quantum = Decimal("0.000001")
    else:
        quantum = Decimal("0.00000001")
    text = format(value.quantize(quantum), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def format_usd(value: float | None) -> str:
    if value is None:
        return ""
    sign = "-" if value < 0 else ""
    number = abs(float(value))
    if number >= 1_000_000:
        return f"{sign}${number / 1_000_000:.2f}M"
    if number >= 10_000:
        return f"{sign}${number / 1000:.1f}k"
    if 0 < number < 0.01:
        return f"{sign}<$0.01"
    return f"{sign}${number:,.2f}"


def price_symbol(symbol: str) -> str:
    key = (symbol or "").upper().replace(".", "")
    if key in {"WETH", "ETH"}:
        return "ETH"
    if key in {"WNEAR", "NEAR"}:
        return "NEAR"
    if key in {"USDBC", "USDC.E", "USDCE"}:
        return "USDC"
    if key in {"CBBTC", "WBTC"}:
        return "BTC"
    return key


def usd_value(symbol: str, amount: Decimal, prices: dict[str, float]) -> float | None:
    key = price_symbol(symbol)
    price = prices.get(key)
    if price is None and key in {"USDC", "USDT", "DAI", "USDBC"}:
        price = 1.0
    if price is None:
        return None
    return float(to_decimal(amount) * Decimal(str(price)))


def parse_time(value: object) -> int | None:
    """Epoch seconds from an ISO string, unix seconds, or NEAR nanoseconds."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if number > 10_000_000_000_000:
            return int(number / 1_000_000_000)
        if number > 10_000_000_000:
            return int(number / 1000)
        return int(number)
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return parse_time(int(text))
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())
    except ValueError:
        return None


def format_time(ts: int | None) -> str:
    if not ts:
        return "unknown time"
    moment = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    return moment.strftime("%Y-%m-%d %H:%M UTC")


def short_address(address: str) -> str:
    text = address or ""
    if not text:
        return ""
    if text.endswith(".near") or text.endswith(".tg") or len(text) <= 18:
        return text
    if text.startswith("0x") and len(text) > 12:
        return text[:6] + "…" + text[-4:]
    if len(text) > 16:
        return text[:4] + "…" + text[-4:]
    return text
