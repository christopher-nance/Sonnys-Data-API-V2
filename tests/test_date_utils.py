"""Tests for date range parsing and validation utilities."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
from zoneinfo import ZoneInfo

from sonnys_data_client._date_utils import parse_date_range


# ---------------------------------------------------------------------------
# Valid inputs
# ---------------------------------------------------------------------------


class TestParseDateRangeValidInputs:
    """Tests for parse_date_range() with valid inputs."""

    def test_iso_date_only_pair(self) -> None:
        """Date-only strings get boundary times (00:00:01 / 23:59:59) in UTC."""
        start, end = parse_date_range("2026-01-01", "2026-01-31")

        assert start == datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

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

        assert start == datetime(2026, 6, 1, 0, 0, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)

    def test_same_day(self) -> None:
        """Same day is valid; start gets 00:00:01, end gets 23:59:59."""
        start, end = parse_date_range("2026-05-15", "2026-05-15")

        assert start == datetime(2026, 5, 15, 0, 0, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 5, 15, 23, 59, 59, tzinfo=timezone.utc)

    def test_naive_datetimes_converted_to_utc(self) -> None:
        """Naive datetimes (no tzinfo) are converted to UTC."""
        dt_start = datetime(2026, 2, 1, 8, 30, 0)
        dt_end = datetime(2026, 2, 28, 17, 0, 0)

        start, end = parse_date_range(dt_start, dt_end)

        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc
        assert start == datetime(2026, 2, 1, 8, 30, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 2, 28, 17, 0, 0, tzinfo=timezone.utc)

    def test_timezone_aware_datetimes_converted_to_utc(self) -> None:
        """Timezone-aware datetimes are converted to UTC."""
        eastern = timezone(timedelta(hours=-5))
        dt_start = datetime(2026, 4, 1, 9, 0, 0, tzinfo=eastern)
        dt_end = datetime(2026, 4, 30, 17, 0, 0, tzinfo=eastern)

        start, end = parse_date_range(dt_start, dt_end)

        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc
        assert start == datetime(2026, 4, 1, 14, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 4, 30, 22, 0, 0, tzinfo=timezone.utc)

    def test_iso_string_with_time_component(self) -> None:
        """ISO strings with time components are parsed correctly."""
        start, end = parse_date_range(
            "2026-01-01T08:00:00", "2026-01-31T23:59:59"
        )

        assert start == datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

    def test_iso_string_with_timezone(self) -> None:
        """ISO strings with timezone info are converted to UTC."""
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


# ---------------------------------------------------------------------------
# Timezone-aware date conversion
# ---------------------------------------------------------------------------


class TestParseDateRangeWithTimezone:
    """Tests for parse_date_range() with site timezone."""

    def test_date_only_chicago(self) -> None:
        """Date-only + Chicago tz: boundaries localized then converted to UTC.

        2026-01-15 in Chicago (CST = UTC-6):
          start 00:00:01 CST → 06:00:01 UTC
          end   23:59:59 CST → 05:59:59 UTC next day
        """
        chicago = ZoneInfo("America/Chicago")
        start, end = parse_date_range("2026-01-15", "2026-01-15", tz=chicago)

        assert start == datetime(2026, 1, 15, 6, 0, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 16, 5, 59, 59, tzinfo=timezone.utc)

    def test_datetime_string_with_tz(self) -> None:
        """Naive datetime string + Chicago tz: localized then converted.

        T08:00:00 in Chicago (CST = UTC-6) → T14:00:00 UTC
        """
        chicago = ZoneInfo("America/Chicago")
        start, end = parse_date_range(
            "2026-01-15T08:00:00", "2026-01-15T20:00:00", tz=chicago
        )

        assert start == datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 16, 2, 0, 0, tzinfo=timezone.utc)

    def test_aware_datetime_ignores_tz_param(self) -> None:
        """Already timezone-aware datetime uses its own tzinfo, not tz param."""
        eastern = timezone(timedelta(hours=-5))
        chicago = ZoneInfo("America/Chicago")

        dt_start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=eastern)
        dt_end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=eastern)

        start, end = parse_date_range(dt_start, dt_end, tz=chicago)

        # Eastern (UTC-5) should be used, not Chicago (UTC-6)
        assert start == datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 15, 22, 0, 0, tzinfo=timezone.utc)

    def test_dst_spring_forward(self) -> None:
        """DST transition: March 8 2026 Chicago springs forward (CST→CDT).

        Before DST (March 7): CST = UTC-6
        After DST (March 8): CDT = UTC-5

        March 7 start 00:00:01 CST → 06:00:01 UTC
        March 8 end   23:59:59 CDT → 04:59:59 UTC next day (UTC-5)
        """
        chicago = ZoneInfo("America/Chicago")
        start, end = parse_date_range("2026-03-07", "2026-03-08", tz=chicago)

        # March 7 is still CST (UTC-6)
        assert start == datetime(2026, 3, 7, 6, 0, 1, tzinfo=timezone.utc)
        # March 8 is CDT (UTC-5) after spring forward
        assert end == datetime(2026, 3, 9, 4, 59, 59, tzinfo=timezone.utc)

    def test_start_after_end_with_tz_raises(self) -> None:
        """start > end still raises ValueError even with timezone."""
        chicago = ZoneInfo("America/Chicago")
        with pytest.raises(
            ValueError, match="start must be before or equal to end"
        ):
            parse_date_range("2026-02-15", "2026-02-01", tz=chicago)

    def test_date_only_without_tz(self) -> None:
        """Date-only without tz: boundaries applied as UTC."""
        start, end = parse_date_range("2026-01-15", "2026-01-15")

        assert start == datetime(2026, 1, 15, 0, 0, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 15, 23, 59, 59, tzinfo=timezone.utc)

    def test_none_tz_behaves_as_utc(self) -> None:
        """Explicitly passing tz=None behaves same as default (UTC)."""
        start, end = parse_date_range("2026-01-15", "2026-01-15", tz=None)

        assert start == datetime(2026, 1, 15, 0, 0, 1, tzinfo=timezone.utc)
        assert end == datetime(2026, 1, 15, 23, 59, 59, tzinfo=timezone.utc)
