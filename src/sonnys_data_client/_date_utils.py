"""Date range parsing and validation utilities.

Shared helpers for normalizing and validating date ranges used by
stat methods across the SDK.  Every stat endpoint (total_sales,
total_washes, conversion_rate, etc.) accepts start/end date
parameters; this module ensures consistent handling.
"""

from __future__ import annotations

from datetime import datetime, timezone


def parse_date_range(
    start: str | datetime,
    end: str | datetime,
) -> tuple[datetime, datetime]:
    """Parse and validate a start/end date range.

    Accepts ISO-8601 strings (e.g. ``"2026-01-01"``) or
    :class:`~datetime.datetime` objects for both arguments and returns
    a validated tuple of timezone-aware datetimes.

    Args:
        start: Range start as an ISO-8601 string or datetime.
        end: Range end as an ISO-8601 string or datetime.

    Returns:
        A ``(start_dt, end_dt)`` tuple of timezone-aware datetimes.
        Naive inputs are assumed UTC; aware inputs are preserved as-is.

    Raises:
        ValueError: If *start* is after *end*, or if a string cannot
            be parsed as a valid ISO-8601 date/datetime.
    """
    start_dt = _normalize(start)
    end_dt = _normalize(end)

    if start_dt > end_dt:
        raise ValueError("start must be before or equal to end")

    return start_dt, end_dt


def _normalize(value: str | datetime) -> datetime:
    """Convert a string or datetime to a timezone-aware datetime.

    Args:
        value: An ISO-8601 string or datetime object.

    Returns:
        A timezone-aware datetime.  Naive values are assigned
        :data:`~datetime.timezone.utc`; aware values pass through
        unchanged.

    Raises:
        ValueError: If *value* is a string that cannot be parsed.
    """
    if isinstance(value, str):
        dt = datetime.fromisoformat(value)
    else:
        dt = value

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt
