"""
Utilities for parsing and formatting human-friendly duration strings.

Accepted formats (case-insensitive):
- Minutes:  "15m" or "15M"
- Hours:    "2h"
- Days:     "1d", "1.5d", "1.25d" (default unit if omitted)
- Weeks:    "1w"

Parsing returns integer minutes. Formatting returns a compact string using
the largest sensible unit with up to two decimal places.
"""

from __future__ import annotations

import math
import re
from typing import Optional

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 24 * 60
MINUTES_PER_WEEK = 7 * MINUTES_PER_DAY


_DUR_RE = re.compile(r"^\s*(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>[mMhHdDwW])?\s*$")


def parse_duration_to_minutes(text: str) -> int:
    """Parse a human duration like "1.5d", "90m", "2h", "1w" to minutes.

    If no unit is provided, defaults to days.
    Raises ValueError on invalid input.
    """
    if text is None:
        raise ValueError("duration is None")
    s = str(text).strip()
    if not s:
        raise ValueError("empty duration")
    m = _DUR_RE.match(s)
    if not m:
        raise ValueError(f"invalid duration: {text!r}")
    val = float(m.group("val"))
    unit = (m.group("unit") or "d").lower()
    if unit == "m":
        minutes = val
    elif unit == "h":
        minutes = val * MINUTES_PER_HOUR
    elif unit == "d":
        minutes = val * MINUTES_PER_DAY
    elif unit == "w":
        minutes = val * MINUTES_PER_WEEK
    else:
        raise ValueError(f"unsupported unit in duration: {text!r}")
    # Round to nearest minute
    return int(round(minutes))


def format_minutes_compact(minutes: Optional[int]) -> str:
    """Format integer minutes into a compact human-readable unit string.

    Examples:
    - 15   -> "15m"
    - 90   -> "1.5h"
    - 1440 -> "1d"
    - 2160 -> "1.5d"
    - 10080 -> "1w"
    """
    if minutes is None:
        return ""
    try:
        m = int(minutes)
    except Exception:
        return ""

    def _fmt(value: float, suffix: str) -> str:
        # Keep up to 2 decimals, trim trailing zeros
        s = f"{value:.2f}".rstrip("0").rstrip(".")
        return f"{s}{suffix}"

    if m >= MINUTES_PER_WEEK:
        return _fmt(m / MINUTES_PER_WEEK, "w")
    if m >= MINUTES_PER_DAY:
        return _fmt(m / MINUTES_PER_DAY, "d")
    if m >= MINUTES_PER_HOUR:
        return _fmt(m / MINUTES_PER_HOUR, "h")
    return f"{m}m"


def ceil_minutes_to_business_days(minutes: int) -> int:
    """Convert minutes to a whole number of business days for date-only back-scheduling.

    Rounds up any fractional day to the next whole day to maintain conservative
    scheduling when only dates (no times) are tracked.
    """
    if minutes is None:
        return 0
    try:
        m = int(minutes)
    except Exception:
        return 0
    # ceil to days; keep minimum of 0
    days = math.ceil(m / MINUTES_PER_DAY) if m > 0 else 0
    return int(days)

