"""Date range parsing and validation utilities.

Shared helpers for normalizing and validating date ranges used by
stat methods across the SDK.  Every stat endpoint (total_sales,
total_washes, conversion_rate, etc.) accepts start/end date
parameters; this module ensures consistent handling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo


def parse_date_range(
    start: str | datetime,
    end: str | datetime,
    *,
    tz: ZoneInfo | None = None,
) -> tuple[datetime, datetime]:
    """Parse and validate a start/end date range.

    Accepts ISO-8601 strings (e.g. ``"2026-01-01"``) or
    :class:`~datetime.datetime` objects for both arguments and returns
    a validated tuple of UTC-normalized datetimes.

    Date-only strings automatically receive boundary times:
    start = 00:00:01, end = 23:59:59.

    When *tz* is provided, naive inputs are interpreted in that
    timezone and converted to UTC.

    Args:
        start: Range start as an ISO-8601 string or datetime.
        end: Range end as an ISO-8601 string or datetime.
        tz: Optional site timezone for localizing naive inputs.

    Returns:
        A ``(start_dt, end_dt)`` tuple of UTC-normalized datetimes.

    Raises:
        ValueError: If *start* is after *end*, or if a string cannot
            be parsed as a valid ISO-8601 date/datetime.
    """
    start_dt = _normalize(start, tz=tz, role="start")
    end_dt = _normalize(end, tz=tz, role="end")

    if start_dt > end_dt:
        raise ValueError("start must be before or equal to end")

    return start_dt, end_dt


def _normalize(
    value: str | datetime,
    *,
    tz: ZoneInfo | None = None,
    role: Literal["start", "end"] = "start",
) -> datetime:
    """Convert a string or datetime to a UTC-normalized datetime.

    Args:
        value: An ISO-8601 string or datetime object.
        tz: Optional timezone for localizing naive inputs.
        role: ``"start"`` or ``"end"`` — controls which boundary time
            is applied to date-only strings.

    Returns:
        A timezone-aware datetime normalized to UTC.

    Raises:
        ValueError: If *value* is a string that cannot be parsed.
    """
    date_only = isinstance(value, str) and "T" not in value

    if isinstance(value, str):
        if date_only:
            # Apply boundary times: start → 00:00:01, end → 23:59:59
            if role == "start":
                value = value + "T00:00:01"
            else:
                value = value + "T23:59:59"
        dt = datetime.fromisoformat(value)
    else:
        dt = value

    # Already timezone-aware → convert to UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)

    # Naive + tz provided → localize then convert to UTC
    if tz is not None:
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)

    # Naive + no tz → assign UTC directly
    return dt.replace(tzinfo=timezone.utc)
