"""Tests for date range parsing and validation utilities."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from sonnys_data_client._date_utils import parse_date_range


# ---------------------------------------------------------------------------
# Valid inputs
# ---------------------------------------------------------------------------


class TestParseDateRangeValidInputs:
    """Tests for parse_date_range() with valid inputs."""

    def test_iso_string_pair(self) -> None:
        """ISO string pair returns validated UTC datetime tuple."""
        start, end = parse_date_range("2026-01-01", "2026-01-31")

        assert start == datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 31, tzinfo=timezone.utc)

    def test_datetime_pair(self) -> None:
        """Datetime pair passes through with UTC normalization."""
        dt_start = datetime(2026, 3, 1)
        dt_end = datetime(2026, 3, 15)

        start, end = parse_date_range(dt_start, dt_end)

        assert start == datetime(2026, 3, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 3, 15, tzinfo=timezone.utc)

    def test_mixed_string_start_datetime_end(self) -> None:
        """Mixed types (string start, datetime end) are both normalized."""
        dt_end = datetime(2026, 6, 30, 12, 0, 0)

        start, end = parse_date_range("2026-06-01", dt_end)

        assert start == datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)

    def test_same_day(self) -> None:
        """Same day (start == end) is valid and returns equal datetimes."""
        start, end = parse_date_range("2026-05-15", "2026-05-15")

        assert start == end
        assert start == datetime(2026, 5, 15, tzinfo=timezone.utc)

    def test_naive_datetimes_converted_to_utc(self) -> None:
        """Naive datetimes (no tzinfo) are converted to UTC."""
        dt_start = datetime(2026, 2, 1, 8, 30, 0)
        dt_end = datetime(2026, 2, 28, 17, 0, 0)

        start, end = parse_date_range(dt_start, dt_end)

        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc
        assert start == datetime(2026, 2, 1, 8, 30, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 2, 28, 17, 0, 0, tzinfo=timezone.utc)

    def test_timezone_aware_datetimes_preserved(self) -> None:
        """Timezone-aware datetimes are preserved as-is."""
        eastern = timezone(timedelta(hours=-5))
        dt_start = datetime(2026, 4, 1, 9, 0, 0, tzinfo=eastern)
        dt_end = datetime(2026, 4, 30, 17, 0, 0, tzinfo=eastern)

        start, end = parse_date_range(dt_start, dt_end)

        assert start.tzinfo == eastern
        assert end.tzinfo == eastern
        assert start == dt_start
        assert end == dt_end

    def test_iso_string_with_time_component(self) -> None:
        """ISO strings with time components are parsed correctly."""
        start, end = parse_date_range(
            "2026-01-01T08:00:00", "2026-01-31T23:59:59"
        )

        assert start == datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

    def test_iso_string_with_timezone(self) -> None:
        """ISO strings with timezone info preserve the timezone."""
        start, end = parse_date_range(
            "2026-01-01T08:00:00+00:00", "2026-01-31T23:59:59+00:00"
        )

        assert start == datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------


class TestParseDateRangeInvalidInputs:
    """Tests for parse_date_range() with invalid inputs."""

    def test_start_after_end_raises_value_error(self) -> None:
        """start > end raises ValueError with descriptive message."""
        with pytest.raises(
            ValueError, match="start must be before or equal to end"
        ):
            parse_date_range("2026-02-15", "2026-02-01")

    def test_start_after_end_datetimes_raises_value_error(self) -> None:
        """start > end with datetime objects raises ValueError."""
        with pytest.raises(
            ValueError, match="start must be before or equal to end"
        ):
            parse_date_range(
                datetime(2026, 12, 31, tzinfo=timezone.utc),
                datetime(2026, 1, 1, tzinfo=timezone.utc),
            )

    def test_invalid_start_string_raises_value_error(self) -> None:
        """Invalid start string raises ValueError."""
        with pytest.raises(ValueError):
            parse_date_range("not-a-date", "2026-01-31")

    def test_invalid_end_string_raises_value_error(self) -> None:
        """Invalid end string raises ValueError."""
        with pytest.raises(ValueError):
            parse_date_range("2026-01-01", "garbage")

    def test_empty_string_raises_value_error(self) -> None:
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            parse_date_range("", "2026-01-31")
