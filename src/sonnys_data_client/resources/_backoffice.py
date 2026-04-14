"""BackOffice web-UI scraper resource.

Pulls the Sonny's BackOffice ``/report/employee-timesheets`` page as an
authenticated user, parses the rendered HTML into structured models, and
returns per-shift, per-employee, and period-total views of timeclock data.

This is an alternative to :meth:`StatsResource.total_labor_cost` — it is
far faster on large date ranges because the BackOffice report renders
every employee across every site in a single HTTP round trip, whereas the
Data API path iterates every employee in 14-day windows.

Requires two additional credentials on the parent :class:`SonnysClient`:
``backoffice_username`` and ``backoffice_password``. These are distinct
from the API credentials because BackOffice is the manager-facing web UI,
not the programmatic API.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup, Tag

from sonnys_data_client._exceptions import (
    BackOfficeCredentialsError,
    BackOfficeLoginError,
    BackOfficeScrapeError,
)
from sonnys_data_client._resources import BaseResource
from sonnys_data_client.types._backoffice import (
    BackOfficeTimeclockResult,
    EmployeeTimesheet,
    TimesheetShift,
)

if TYPE_CHECKING:
    from sonnys_data_client._client import SonnysClient

logger = logging.getLogger("sonnys_data_client")

_MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

_EMPLOYEE_HEADER_RE = re.compile(
    r"^(?P<name>.+?)\s*\(#(?P<num>\d+)(?:,\s*ADP ID:\s*(?P<adp>[^)]+))?\)\s*$"
)

_PERIOD_RE = re.compile(
    r"Period of\s*(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})"
)


class BackOfficeResource(BaseResource):
    """Scraper for the BackOffice employee timesheets report.

    Requires ``backoffice_username`` and ``backoffice_password`` at
    :class:`SonnysClient` construction. The ``api_id`` doubles as the
    BackOffice subdomain (e.g. ``"washu"`` →
    ``https://washu.sonnyscontrols.com``).
    """

    LOGIN_PATH = "/login"
    LOGIN_CHECK_PATH = "/login_check"
    TIMESHEETS_PATH = "/report/employee-timesheets"

    _USER_AGENT = "sonnys-data-client/backoffice"
    _REQUEST_TIMEOUT = 30
    _REPORT_TIMEOUT = 120

    def __init__(self, client: SonnysClient) -> None:
        super().__init__(client)

    # -- Public API ---------------------------------------------------------

    def timeclock(
        self,
        start: str | date | datetime,
        end: str | date | datetime,
        *,
        site_id: int | None = None,
    ) -> BackOfficeTimeclockResult:
        """Scrape the employee-timesheets report for a date range.

        Returns per-shift punch-in/out detail grouped by employee, plus a
        period grand total parsed from the report's footer row.

        The client-level ``site_code`` is **not** applied here. The
        BackOffice report is returned for all sites and every shift
        carries its own ``site_code`` field. Pass an explicit numeric
        ``site_id`` (the BackOffice URL parameter) to narrow at fetch
        time, or filter ``result.employees[*].shifts`` locally.

        Args:
            start: Start date (inclusive) as ``YYYY-MM-DD`` string,
                :class:`~datetime.date`, or :class:`~datetime.datetime`.
            end: End date (inclusive), same types.
            site_id: Optional numeric BackOffice site id for URL-level
                filtering. When ``None`` the report includes all sites.

        Returns:
            A :class:`BackOfficeTimeclockResult` with the full parsed
            report.

        Raises:
            BackOfficeCredentialsError: ``backoffice_username`` or
                ``backoffice_password`` was not supplied.
            BackOfficeLoginError: BackOffice authentication failed.
            BackOfficeScrapeError: The page HTML did not match the
                expected structure.
        """
        self._require_credentials()
        start_d = _coerce_date(start)
        end_d = _coerce_date(end)
        if start_d > end_d:
            raise ValueError(f"start ({start_d}) must be <= end ({end_d})")

        session = self._ensure_logged_in()
        html = self._fetch_timesheet_html(session, start_d, end_d, site_id)
        try:
            return _parse_timesheet_page(html)
        except BackOfficeScrapeError:
            raise
        except Exception as e:
            raise BackOfficeScrapeError(
                f"Failed to parse BackOffice timesheets page: {e}"
            ) from e

    # -- Credential / session management -----------------------------------

    def _require_credentials(self) -> None:
        missing = [
            name
            for name, val in (
                ("backoffice_username", self._client._backoffice_username),
                ("backoffice_password", self._client._backoffice_password),
            )
            if val is None
        ]
        if missing:
            raise BackOfficeCredentialsError(
                "BackOffice methods require "
                + ", ".join(missing)
                + " to be supplied when constructing SonnysClient."
            )

    def _base_url(self) -> str:
        return f"https://{self._client.api_id}.sonnyscontrols.com"

    def _ensure_logged_in(self) -> requests.Session:
        if self._client._backoffice_session is not None:
            return self._client._backoffice_session
        return self._login()

    def _login(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": self._USER_AGENT})
        base = self._base_url()

        try:
            session.get(base + self.LOGIN_PATH, timeout=self._REQUEST_TIMEOUT)
        except requests.RequestException as e:
            session.close()
            raise BackOfficeLoginError(
                f"Cannot reach BackOffice login page at {base}: {e}"
            ) from e

        try:
            resp = session.post(
                base + self.LOGIN_CHECK_PATH,
                data={
                    "_username": self._client._backoffice_username,
                    "_password": self._client._backoffice_password,
                },
                timeout=self._REQUEST_TIMEOUT,
                allow_redirects=True,
            )
        except requests.RequestException as e:
            session.close()
            raise BackOfficeLoginError(
                f"BackOffice login request failed: {e}"
            ) from e

        if "/login" in resp.url:
            session.close()
            raise BackOfficeLoginError(
                f"BackOffice login failed — server redirected back to "
                f"{resp.url}. Check backoffice_username / "
                f"backoffice_password."
            )

        logger.info("Authenticated to BackOffice at %s", base)
        self._client._backoffice_session = session
        return session

    # -- Fetch --------------------------------------------------------------

    def _fetch_timesheet_html(
        self,
        session: requests.Session,
        start_d: date,
        end_d: date,
        site_id: int | None,
    ) -> str:
        url = (
            self._base_url()
            + self.TIMESHEETS_PATH
            + "?dateStart="
            + _format_date_for_url(start_d)
            + "&dateEnd="
            + _format_date_for_url(end_d)
            + "&landingPage="
        )
        if site_id is not None:
            url += f"&siteId={site_id}"

        try:
            resp = session.get(url, timeout=self._REPORT_TIMEOUT)
        except requests.RequestException as e:
            raise BackOfficeLoginError(
                f"BackOffice report request failed: {e}"
            ) from e

        if "/login" in resp.url:
            logger.warning("BackOffice session expired, re-authenticating")
            session.close()
            self._client._backoffice_session = None
            session = self._login()
            try:
                resp = session.get(url, timeout=self._REPORT_TIMEOUT)
            except requests.RequestException as e:
                raise BackOfficeLoginError(
                    f"BackOffice report request failed after re-login: {e}"
                ) from e
            if "/login" in resp.url:
                raise BackOfficeLoginError(
                    "BackOffice report still redirects to login after "
                    "re-authenticating."
                )

        if resp.status_code != 200:
            raise BackOfficeScrapeError(
                f"BackOffice report returned HTTP {resp.status_code}"
            )

        return resp.text


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _parse_timesheet_page(html: str) -> BackOfficeTimeclockResult:
    """Parse the full timesheets HTML page into a structured result.

    See :class:`BackOfficeResource` for the expected page structure.
    """
    soup = BeautifulSoup(html, "html.parser")

    period_start, period_end = _parse_period_header(soup)
    employees = _parse_employee_blocks(soup)
    totals = _parse_grand_totals(soup)

    return BackOfficeTimeclockResult(
        period_start=period_start,
        period_end=period_end,
        employees=employees,
        total_regular_hours=totals["regular_hours"],
        total_regular_wages=totals["regular_wages"],
        total_overtime_hours=totals["overtime_hours"],
        total_overtime_wages=totals["overtime_wages"],
        total_wages=totals["total_wages"],
    )


def _parse_period_header(soup: BeautifulSoup) -> tuple[str, str]:
    h3 = soup.find("h3", string=_PERIOD_RE)
    if h3 is None:
        # Sometimes the h3 has whitespace around the text; fall back
        for candidate in soup.find_all("h3"):
            if _PERIOD_RE.search(candidate.get_text(strip=True) or ""):
                h3 = candidate
                break
    if h3 is None:
        raise BackOfficeScrapeError(
            "Could not find 'Period of MM/DD/YYYY - MM/DD/YYYY' header"
        )
    text = h3.get_text(strip=True)
    match = _PERIOD_RE.search(text)
    if match is None:
        raise BackOfficeScrapeError(
            f"Period header text did not match expected format: {text!r}"
        )
    return _parse_date_mdy(match.group(1)), _parse_date_mdy(match.group(2))


def _parse_employee_blocks(soup: BeautifulSoup) -> list[EmployeeTimesheet]:
    employees: list[EmployeeTimesheet] = []
    for title_cell in soup.find_all("td", class_="report-employee-title"):
        strong = title_cell.find("strong")
        if strong is None:
            continue
        header_text = strong.get_text(strip=True)
        match = _EMPLOYEE_HEADER_RE.match(header_text)
        if match is None:
            raise BackOfficeScrapeError(
                f"Could not parse employee header: {header_text!r}"
            )
        employee_name = match.group("name").strip()
        employee_number = int(match.group("num"))
        adp_id = match.group("adp").strip() if match.group("adp") else None

        title_table = title_cell.find_parent("table")
        if title_table is None:
            continue
        detail_table = _next_detail_table(title_table)
        if detail_table is None:
            raise BackOfficeScrapeError(
                f"Could not find detail table for employee {employee_name!r}"
            )

        shifts, rollup = _parse_employee_detail_table(detail_table, employee_name)

        employees.append(
            EmployeeTimesheet(
                employee_name=employee_name,
                employee_number=employee_number,
                adp_id=adp_id,
                shifts=shifts,
                total_regular_hours=rollup["regular_hours"],
                total_regular_wages=rollup["regular_wages"],
                total_overtime_hours=rollup["overtime_hours"],
                total_overtime_wages=rollup["overtime_wages"],
                total_wages=rollup["total_wages"],
            )
        )

    if not employees:
        raise BackOfficeScrapeError(
            "No employee blocks found on the timesheets page"
        )
    return employees


def _next_detail_table(title_table: Tag) -> Tag | None:
    """Find the detail table that follows an employee title table.

    The detail table is recognised by having a ``<th>`` header cell whose
    text is exactly ``Date In``.
    """
    node = title_table
    for _ in range(5):  # bounded walk
        node = node.find_next("table")
        if node is None:
            return None
        first_th = node.find("th")
        if first_th is not None and first_th.get_text(strip=True) == "Date In":
            return node
    return None


def _parse_employee_detail_table(
    table: Tag,
    employee_name: str,
) -> tuple[list[TimesheetShift], dict[str, float | None]]:
    shifts: list[TimesheetShift] = []
    pending_comment: str | None = None
    rollup: dict[str, float | None] | None = None

    tbody = table.find("tbody")
    if tbody is None:
        return shifts, _empty_rollup()

    for tr in tbody.find_all("tr", recursive=False):
        classes = tr.get("class") or []

        # Comment row that annotates the next data row
        if "addon-row-comment" in classes:
            em = tr.find("em")
            pending_comment = em.get_text(strip=True) if em else None
            continue

        # Rollup row ("Total for <name>:")
        if "active" in classes:
            rollup = _parse_employee_rollup_row(tr)
            break

        # Normal data row
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 12:
            continue
        shifts.append(_parse_shift_row(tds, classes, pending_comment))
        pending_comment = None

    if rollup is None:
        raise BackOfficeScrapeError(
            f"Missing rollup row for employee {employee_name!r}"
        )
    return shifts, rollup


def _parse_shift_row(
    tds: list[Tag],
    classes: list[str],
    comment: str | None,
) -> TimesheetShift:
    date_in_text = tds[0].get_text(strip=True)
    time_in_text = tds[1].get_text(strip=True)
    date_out_text = tds[2].get_text(strip=True)
    time_out_text = tds[3].get_text(strip=True)
    site_code = tds[4].get_text(strip=True)
    regular_rate = _parse_dollar(tds[5].get_text(strip=True))
    regular_hours = _parse_float(tds[6].get_text(strip=True))
    regular_wages = _parse_dollar(tds[7].get_text(strip=True))
    overtime_rate = _parse_dollar_or_none(tds[8].get_text(strip=True))
    overtime_hours = _parse_float_or_none(tds[9].get_text(strip=True))
    overtime_wages = _parse_dollar_or_none(tds[10].get_text(strip=True))
    total_wages = _parse_dollar(tds[11].get_text(strip=True))

    time_in, tz_in = _split_time_and_tz(time_in_text)
    time_out, _ = _split_time_and_tz(time_out_text)

    return TimesheetShift(
        date_in=_parse_date_mdy(date_in_text),
        time_in=time_in,
        date_out=_parse_date_mdy(date_out_text),
        time_out=time_out,
        timezone=tz_in,
        site_code=site_code,
        regular_rate=regular_rate,
        regular_hours=regular_hours,
        regular_wages=regular_wages,
        overtime_rate=overtime_rate,
        overtime_hours=overtime_hours,
        overtime_wages=overtime_wages,
        total_wages=total_wages,
        was_modified="warning" in classes,
        was_created_in_back_office="danger" in classes,
        comment=comment,
    )


def _parse_employee_rollup_row(tr: Tag) -> dict[str, float | None]:
    """Extract totals from a '<tr class="active">' rollup row.

    The row layout is: one leading <th> spanning columns (the label),
    followed by <th> cells mirroring the detail-table columns from
    Regular Rate onwards.
    """
    ths = tr.find_all("th")
    # ths[0] is the label ("Total for Name:"), ths[1] is an empty
    # regular-rate placeholder. Values we care about are indexed
    # relative to the END of the row so we survive minor column shifts.
    texts = [th.get_text(strip=True) for th in ths]
    if len(texts) < 7:
        raise BackOfficeScrapeError(
            f"Unexpected rollup row structure: {texts!r}"
        )
    # Last 7 cells: [regular_rate(blank), regular_hours, regular_wages,
    #                overtime_rate(blank), overtime_hours, overtime_wages,
    #                total_wages]
    tail = texts[-7:]
    return {
        "regular_hours": _parse_float(tail[1]),
        "regular_wages": _parse_dollar(tail[2]),
        "overtime_hours": _parse_float_or_none(tail[4]),
        "overtime_wages": _parse_dollar_or_none(tail[5]),
        "total_wages": _parse_dollar(tail[6]),
    }


def _empty_rollup() -> dict[str, float | None]:
    return {
        "regular_hours": 0.0,
        "regular_wages": 0.0,
        "overtime_hours": None,
        "overtime_wages": None,
        "total_wages": 0.0,
    }


def _parse_grand_totals(soup: BeautifulSoup) -> dict[str, float]:
    """Find the final 'Timesheet Total:' row and extract the grand totals."""
    for tr in soup.find_all("tr"):
        first_th = tr.find("th")
        if first_th is None:
            continue
        if first_th.get_text(strip=True) == "Timesheet Total:":
            tds = tr.find_all("td")
            # The row contains 7 <td> values (matching the 7 numeric
            # columns in the footer's thead).
            if len(tds) < 7:
                raise BackOfficeScrapeError(
                    f"Unexpected Timesheet Total row structure "
                    f"({len(tds)} <td> cells)"
                )
            texts = [td.get_text(strip=True) for td in tds]
            tail = texts[-7:]
            return {
                "regular_hours": _parse_float(tail[1]),
                "regular_wages": _parse_dollar(tail[2]),
                "overtime_hours": _parse_float(tail[4]),
                "overtime_wages": _parse_dollar(tail[5]),
                "total_wages": _parse_dollar(tail[6]),
            }

    raise BackOfficeScrapeError("Could not find 'Timesheet Total:' footer row")


# ---------------------------------------------------------------------------
# Small parsing primitives
# ---------------------------------------------------------------------------


def _parse_dollar(text: str) -> float:
    """Parse '$1,234.56' → 1234.56. Treats blank/missing as 0.0."""
    if not text:
        return 0.0
    cleaned = text.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0.0
    return float(cleaned)


def _parse_dollar_or_none(text: str) -> float | None:
    """Like :func:`_parse_dollar` but returns None for 'n/a' cells."""
    if not text or text.strip().lower() == "n/a":
        return None
    stripped = text.replace("$", "").replace(",", "").strip()
    if not stripped:
        return None
    return float(stripped)


def _parse_float(text: str) -> float:
    if not text:
        return 0.0
    return float(text.replace(",", "").strip())


def _parse_float_or_none(text: str) -> float | None:
    if not text or text.strip().lower() == "n/a":
        return None
    return float(text.replace(",", "").strip())


def _parse_date_mdy(text: str) -> str:
    """Convert 'MM/DD/YYYY' to ISO 'YYYY-MM-DD'."""
    parts = text.strip().split("/")
    if len(parts) != 3:
        raise BackOfficeScrapeError(f"Unexpected date format: {text!r}")
    month, day, year = parts
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def _split_time_and_tz(text: str) -> tuple[str, str]:
    """Split '2:10 PM (CST)' into ('2:10 PM', 'CST').

    The BackOffice detail rows embed the timezone in parens alongside
    the time. If no parens are present, timezone defaults to ''.
    """
    text = text.strip()
    if not text:
        return "", ""
    if "(" in text and text.endswith(")"):
        time_part, tz_part = text.rsplit("(", 1)
        return time_part.strip(), tz_part.rstrip(")").strip()
    return text, ""


def _coerce_date(value: date | str | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _format_date_for_url(d: date) -> str:
    """Format a date as 'Mon+DD%2C+YYYY' for the BackOffice URL."""
    return f"{_MONTHS[d.month - 1]}+{d.day}%2C+{d.year}"
