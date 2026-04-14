"""Tests for the BackOffice web-UI scraper resource.

Covers:
- Credential guard on :class:`SonnysClient` when BackOffice creds absent
- Backwards compatibility: constructing a client without BackOffice
  creds must still succeed
- Parser fidelity against a captured HTML fixture
- Small parsing primitive helpers
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from sonnys_data_client import (
    BackOfficeCredentialsError,
    BackOfficeTimeclockResult,
    SonnysClient,
)
from sonnys_data_client.resources._backoffice import (
    _coerce_date,
    _format_date_for_url,
    _parse_date_mdy,
    _parse_dollar,
    _parse_dollar_or_none,
    _parse_float,
    _parse_float_or_none,
    _parse_timesheet_page,
    _split_time_and_tz,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "backoffice_timesheets_sample.html"
OPEN_SHIFT_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "backoffice_timesheets_open_shifts.html"
)
EMPTY_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "backoffice_timesheets_empty.html"
)


@pytest.fixture()
def sample_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture()
def parsed(sample_html: str) -> BackOfficeTimeclockResult:
    return _parse_timesheet_page(sample_html)


@pytest.fixture()
def open_shift_html() -> str:
    return OPEN_SHIFT_FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture()
def parsed_open(open_shift_html: str) -> BackOfficeTimeclockResult:
    return _parse_timesheet_page(open_shift_html)


# ---------------------------------------------------------------------------
# Credential guard + backwards compatibility
# ---------------------------------------------------------------------------


class TestCredentialGuard:
    def test_no_backoffice_creds_raises_on_method_call(self) -> None:
        """Calling BackOffice methods without creds raises with a
        message that names every missing field."""
        client = SonnysClient("washu", "key")
        try:
            with pytest.raises(BackOfficeCredentialsError) as excinfo:
                client.backoffice.timeclock("2026-03-01", "2026-03-02")
            msg = str(excinfo.value)
            assert "backoffice_username" in msg
            assert "backoffice_password" in msg
        finally:
            client.close()

    def test_partial_backoffice_creds_still_raises(self) -> None:
        """Supplying only one of the two BackOffice fields is treated
        as unconfigured and the missing field is reported."""
        client = SonnysClient(
            "washu", "key", backoffice_username="admin"
        )
        try:
            with pytest.raises(BackOfficeCredentialsError) as excinfo:
                client.backoffice.timeclock("2026-03-01", "2026-03-02")
            msg = str(excinfo.value)
            assert "backoffice_password" in msg
            assert "backoffice_username" not in msg
        finally:
            client.close()

    def test_backwards_compat_construct_without_backoffice_creds(self) -> None:
        """The existing SonnysClient(api_id, api_key) constructor still
        works with zero BackOffice configuration and leaves the lazy
        session as None."""
        client = SonnysClient("washu", "key")
        try:
            assert client._backoffice_session is None
            # The .backoffice property should still be accessible
            # (constructing the resource is cheap and credential-free)
            assert client.backoffice is not None
        finally:
            client.close()


# ---------------------------------------------------------------------------
# Parser fidelity against the sample HTML fixture
# ---------------------------------------------------------------------------


class TestPeriodHeader:
    def test_period_dates_parsed_to_iso(self, parsed: BackOfficeTimeclockResult) -> None:
        assert parsed.period_start == "2026-03-02"
        assert parsed.period_end == "2026-03-03"


class TestEmployeeCount:
    def test_six_employees_in_fixture(self, parsed: BackOfficeTimeclockResult) -> None:
        names = [e.employee_name for e in parsed.employees]
        assert names == [
            "Almaliki, Moustafa",
            "Anderson, Leilani",
            "Ballard, Joel",
            "Barker, Jacob",
            "Bedford, Kameron",
            "Pina, Angelica",
        ]


class TestSimpleSingleShift:
    """Anderson, Leilani — one shift, regular pay, zero overtime."""

    def test_employee_rollup(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(e for e in parsed.employees if e.employee_name == "Anderson, Leilani")
        assert emp.employee_number == 423
        assert emp.adp_id is None
        assert len(emp.shifts) == 1
        assert emp.total_regular_hours == pytest.approx(6.14)
        assert emp.total_regular_wages == pytest.approx(92.10)
        assert emp.total_overtime_hours == pytest.approx(0.0)
        assert emp.total_overtime_wages == pytest.approx(0.0)
        assert emp.total_wages == pytest.approx(92.10)

    def test_shift_detail(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(e for e in parsed.employees if e.employee_name == "Anderson, Leilani")
        shift = emp.shifts[0]
        assert shift.date_in == "2026-03-02"
        assert shift.date_out == "2026-03-02"
        assert shift.time_in == "1:59 PM"
        assert shift.time_out == "8:08 PM"
        assert shift.timezone == "CST"
        assert shift.site_code == "EVRGRN"
        assert shift.regular_rate == pytest.approx(15.0)
        assert shift.regular_hours == pytest.approx(6.14)
        assert shift.regular_wages == pytest.approx(92.10)
        assert shift.overtime_rate == pytest.approx(22.50)
        assert shift.overtime_hours == pytest.approx(0.0)
        assert shift.overtime_wages == pytest.approx(0.0)
        assert shift.total_wages == pytest.approx(92.10)
        assert shift.was_modified is False
        assert shift.was_created_in_back_office is False
        assert shift.comment is None


class TestMultiShiftSameDay:
    """Ballard, Joel — 2 shifts on 03/02 at JOLIET."""

    def test_two_shifts_on_same_date(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(e for e in parsed.employees if e.employee_name == "Ballard, Joel")
        assert len(emp.shifts) == 2
        assert all(s.date_in == "2026-03-02" for s in emp.shifts)
        assert all(s.site_code == "JOLIET" for s in emp.shifts)
        # 0.01 + 6.97 = 6.98
        assert emp.total_regular_hours == pytest.approx(6.98)
        assert emp.total_regular_wages == pytest.approx(104.70)
        assert emp.total_wages == pytest.approx(104.70)


class TestNaOvertime:
    """Almaliki, Moustafa — overtime columns are 'n/a' (not eligible)."""

    def test_overtime_fields_are_none(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(
            e for e in parsed.employees if e.employee_name == "Almaliki, Moustafa"
        )
        assert len(emp.shifts) == 2
        for shift in emp.shifts:
            assert shift.overtime_rate is None
            assert shift.overtime_hours is None
            assert shift.overtime_wages is None
        # The employee-level rollup also surfaces None for OT fields
        assert emp.total_overtime_hours is None
        assert emp.total_overtime_wages is None
        # Regular rate was $0.00 in the sample — treated as 0.0
        assert all(s.regular_rate == 0.0 for s in emp.shifts)
        assert emp.total_regular_hours == pytest.approx(14.58)


class TestAdpIdSuffix:
    """Barker, Jacob (#391, ADP ID: 1140) — header suffix parsing."""

    def test_adp_id_extracted(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(e for e in parsed.employees if e.employee_name == "Barker, Jacob")
        assert emp.employee_number == 391
        assert emp.adp_id == "1140"


class TestModifiedEntry:
    """Bedford, Kameron — single warning-class shift with comment."""

    def test_was_modified_and_comment(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(
            e for e in parsed.employees if e.employee_name == "Bedford, Kameron"
        )
        assert len(emp.shifts) == 1
        shift = emp.shifts[0]
        assert shift.was_modified is True
        assert shift.was_created_in_back_office is False
        assert shift.comment is not None
        assert shift.comment.startswith("This entry was modified")


class TestBackOfficeCreatedEntry:
    """Pina, Angelica — danger-class shift with 'created from Back Office'."""

    def test_created_flag_and_comment(self, parsed: BackOfficeTimeclockResult) -> None:
        emp = next(e for e in parsed.employees if e.employee_name == "Pina, Angelica")
        shift = emp.shifts[0]
        assert shift.was_modified is False
        assert shift.was_created_in_back_office is True
        assert shift.comment is not None
        assert "Back Office" in shift.comment
        assert "4got to punch in" in shift.comment


class TestGrandTotals:
    """The Timesheet Total: footer row yields the top-level totals."""

    def test_grand_totals(self, parsed: BackOfficeTimeclockResult) -> None:
        assert parsed.total_regular_hours == pytest.approx(807.98)
        assert parsed.total_regular_wages == pytest.approx(11304.99)
        assert parsed.total_overtime_hours == pytest.approx(0.0)
        assert parsed.total_overtime_wages == pytest.approx(0.0)
        assert parsed.total_wages == pytest.approx(11304.99)


# ---------------------------------------------------------------------------
# Parsing primitive helpers
# ---------------------------------------------------------------------------


class TestParseDollar:
    def test_plain(self) -> None:
        assert _parse_dollar("$15.00") == 15.0

    def test_with_thousands_sep(self) -> None:
        assert _parse_dollar("$11,304.99") == 11304.99

    def test_zero(self) -> None:
        assert _parse_dollar("$0.00") == 0.0

    def test_empty(self) -> None:
        assert _parse_dollar("") == 0.0


class TestParseDollarOrNone:
    def test_na_returns_none(self) -> None:
        assert _parse_dollar_or_none("n/a") is None
        assert _parse_dollar_or_none("N/A") is None

    def test_number_parsed(self) -> None:
        assert _parse_dollar_or_none("$22.50") == 22.5

    def test_empty_returns_none(self) -> None:
        assert _parse_dollar_or_none("") is None


class TestParseFloatOrNone:
    def test_na_returns_none(self) -> None:
        assert _parse_float_or_none("n/a") is None

    def test_number_parsed(self) -> None:
        assert _parse_float_or_none("7.32") == 7.32

    def test_plain_float(self) -> None:
        assert _parse_float("6.14") == 6.14


class TestParseDateMdy:
    def test_basic(self) -> None:
        assert _parse_date_mdy("03/02/2026") == "2026-03-02"

    def test_padding(self) -> None:
        assert _parse_date_mdy("3/2/2026") == "2026-03-02"


class TestSplitTimeAndTz:
    def test_with_tz(self) -> None:
        assert _split_time_and_tz("2:10 PM (CST)") == ("2:10 PM", "CST")

    def test_without_tz(self) -> None:
        assert _split_time_and_tz("2:10 PM") == ("2:10 PM", "")

    def test_empty(self) -> None:
        assert _split_time_and_tz("") == ("", "")


class TestCoerceDate:
    def test_string(self) -> None:
        assert _coerce_date("2026-03-01") == date(2026, 3, 1)

    def test_date(self) -> None:
        d = date(2026, 3, 1)
        assert _coerce_date(d) is d


class TestFormatDateForUrl:
    def test_march(self) -> None:
        assert _format_date_for_url(date(2026, 3, 1)) == "Mar+1%2C+2026"

    def test_december(self) -> None:
        assert _format_date_for_url(date(2025, 12, 31)) == "Dec+31%2C+2025"


# ---------------------------------------------------------------------------
# Open-shift (still clocked in) fixture
# ---------------------------------------------------------------------------


class TestOpenShiftPeriodAndCount:
    """Fixture captures a present-day report with in-progress shifts."""

    def test_period(self, parsed_open: BackOfficeTimeclockResult) -> None:
        assert parsed_open.period_start == "2026-04-14"
        assert parsed_open.period_end == "2026-04-14"

    def test_employees(self, parsed_open: BackOfficeTimeclockResult) -> None:
        names = [e.employee_name for e in parsed_open.employees]
        assert names == [
            "Alvarez, Jaime",
            "Anderson, Tre",
            "Austin, Brianna",
            "Banks, Gregory",
            "Barker, Jacob",
        ]


class TestFullyOpenShift:
    """Anderson, Tre -- single shift, still clocked in, n/a overtime."""

    def test_is_open(self, parsed_open: BackOfficeTimeclockResult) -> None:
        emp = next(e for e in parsed_open.employees if e.employee_name == "Anderson, Tre")
        assert len(emp.shifts) == 1
        shift = emp.shifts[0]
        assert shift.is_open is True
        assert shift.date_out is None
        assert shift.time_out is None
        # Clock-in data is still populated
        assert shift.date_in == "2026-04-14"
        assert shift.time_in == "6:55 AM"
        assert shift.timezone == "CDT"
        assert shift.site_code == "WHEAT"
        # BackOffice accumulates partial hours/wages for the open shift
        assert shift.regular_hours == pytest.approx(5.05)
        assert shift.regular_wages == pytest.approx(0.0)
        assert shift.overtime_rate is None
        assert shift.overtime_hours is None


class TestMixedClosedAndOpenShifts:
    """Alvarez, Jaime -- one closed shift + one open shift on the same day."""

    def test_two_shifts_one_open(self, parsed_open: BackOfficeTimeclockResult) -> None:
        emp = next(
            e for e in parsed_open.employees if e.employee_name == "Alvarez, Jaime"
        )
        assert len(emp.shifts) == 2

        closed, open_shift = emp.shifts
        assert closed.is_open is False
        assert closed.date_out == "2026-04-14"
        assert closed.time_out == "11:05 AM"
        assert closed.regular_hours == pytest.approx(4.38)
        assert closed.regular_wages == pytest.approx(70.08)

        assert open_shift.is_open is True
        assert open_shift.date_out is None
        assert open_shift.time_out is None
        assert open_shift.date_in == "2026-04-14"
        assert open_shift.time_in == "11:35 AM"
        assert open_shift.regular_hours == pytest.approx(0.38)
        assert open_shift.regular_wages == pytest.approx(6.08)

    def test_employee_rollup_includes_open_shift_wages(
        self, parsed_open: BackOfficeTimeclockResult
    ) -> None:
        """BackOffice sums partial open-shift wages into the employee total."""
        emp = next(
            e for e in parsed_open.employees if e.employee_name == "Alvarez, Jaime"
        )
        assert emp.total_regular_hours == pytest.approx(4.76)
        assert emp.total_regular_wages == pytest.approx(76.16)
        assert emp.total_wages == pytest.approx(76.16)


class TestOpenShiftPreservesMetadata:
    """Open shifts still report ADP IDs, site codes, and paid-rate data."""

    def test_adp_id_with_open_shift(
        self, parsed_open: BackOfficeTimeclockResult
    ) -> None:
        emp = next(e for e in parsed_open.employees if e.employee_name == "Barker, Jacob")
        assert emp.adp_id == "1140"
        assert len(emp.shifts) == 1
        assert emp.shifts[0].is_open is True

    def test_paid_rate_on_open_shift(
        self, parsed_open: BackOfficeTimeclockResult
    ) -> None:
        emp = next(e for e in parsed_open.employees if e.employee_name == "Banks, Gregory")
        shift = emp.shifts[0]
        assert shift.is_open is True
        assert shift.regular_rate == pytest.approx(20.0)
        assert shift.regular_hours == pytest.approx(6.48)
        assert shift.regular_wages == pytest.approx(129.60)
        assert shift.overtime_rate == pytest.approx(30.0)


class TestOpenShiftGrandTotals:
    """Period grand totals parse correctly on a present-day report."""

    def test_grand_totals(self, parsed_open: BackOfficeTimeclockResult) -> None:
        assert parsed_open.total_regular_hours == pytest.approx(131.54)
        assert parsed_open.total_regular_wages == pytest.approx(1747.15)
        assert parsed_open.total_wages == pytest.approx(1747.15)


# ---------------------------------------------------------------------------
# Empty-result fixture (no clock entries for the requested range)
# ---------------------------------------------------------------------------


class TestEmptyResult:
    """BackOffice returns a single <h3> when no clock entries exist."""

    def test_parses_to_zero_result(self) -> None:
        html = EMPTY_FIXTURE_PATH.read_text(encoding="utf-8")
        result = _parse_timesheet_page(
            html,
            request_start="2030-01-05",
            request_end="2030-01-05",
        )
        assert result.employees == []
        assert result.period_start == "2030-01-05"
        assert result.period_end == "2030-01-05"
        assert result.total_regular_hours == 0.0
        assert result.total_regular_wages == 0.0
        assert result.total_overtime_hours == 0.0
        assert result.total_overtime_wages == 0.0
        assert result.total_wages == 0.0

    def test_request_range_defaults_to_empty_strings(self) -> None:
        """When called without request_start/end (e.g. from tests), the
        period fields fall back to empty strings rather than crashing."""
        html = EMPTY_FIXTURE_PATH.read_text(encoding="utf-8")
        result = _parse_timesheet_page(html)
        assert result.employees == []
        assert result.period_start == ""
        assert result.period_end == ""
        assert result.total_wages == 0.0

    def test_detects_sentinel_in_noisy_html(self) -> None:
        """The empty-state h3 can appear inside arbitrary surrounding markup."""
        html = """
        <div class="main-column-full-width">
          <div class="some-wrapper">
            <h3 class="text-center nix-bm">
              No clock entries found matching the given criteria.
            </h3>
          </div>
        </div>
        """
        result = _parse_timesheet_page(
            html, request_start="2030-01-05", request_end="2030-01-05"
        )
        assert result.employees == []
        assert result.total_wages == 0.0
