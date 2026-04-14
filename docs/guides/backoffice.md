# BackOffice

The **BackOffice** resource scrapes the Sonny's BackOffice web UI (the
manager portal, e.g. `https://washu.sonnyscontrols.com`) to retrieve
timeclock data far faster than the Data API path can. The BackOffice
employee-timesheets report returns every employee across every site for
an entire month in a single authenticated page load, whereas
`client.stats.total_labor_cost()` must iterate every employee in 14-day
windows against the API rate limit.

!!! info "When to use this vs. `stats.total_labor_cost()`"
    Use `client.backoffice.timeclock()` when you need **fast, bulk,
    per-shift** detail — especially for multi-site operators or date
    ranges of a week or more. Use `client.stats.total_labor_cost()`
    when you only need aggregated totals and you don't want a second
    credential set. Both methods coexist; neither replaces the other.

## Credentials

The BackOffice scraper requires **two additional credentials** on top of
the regular API ID and key, passed at client construction:

```python
from sonnys_data_client import SonnysClient

with SonnysClient(
    api_id="washu",                         # doubles as BackOffice subdomain
    api_key="your-api-key",
    backoffice_username="your.manager.login",
    backoffice_password="your-backoffice-password",
) as client:
    result = client.backoffice.timeclock("2026-03-01", "2026-03-31")
```

!!! warning "`api_id` doubles as the BackOffice subdomain"
    The BackOffice base URL is `https://{api_id}.sonnyscontrols.com`.
    For a WashU site the `api_id` is `"washu"` and the BackOffice login
    lives at `https://washu.sonnyscontrols.com/login`. Pass your tenant
    identifier as the `api_id` argument — same value you already use for
    the Data API.

!!! note "BackOffice credentials are NOT the same as API credentials"
    The BackOffice user is a **manager-portal** account that can log in
    to the web UI. It is a different credential set from
    `X-Sonnys-API-ID` / `X-Sonnys-API-Key`. Provision a dedicated
    BackOffice administrator for the scraper and store its username and
    password in the same secret manager you use for the API credentials.

!!! tip "Backwards compatibility"
    Existing code that constructs `SonnysClient(api_id, api_key)` without
    BackOffice credentials continues to work unchanged. Any attempt to
    call a BackOffice method without having supplied the BackOffice
    credentials raises :class:`BackOfficeCredentialsError` with the
    missing field names.

## Methods

### `timeclock(start, end, *, site_id=None) -> BackOfficeTimeclockResult`

Scrape the `/report/employee-timesheets` page for a date range and
return per-shift punch-in/punch-out detail grouped by employee, plus a
period grand total parsed from the report's footer row.

```python
result = client.backoffice.timeclock("2026-03-01", "2026-03-31")

print(f"Employees: {len(result.employees)}")
print(f"Total wages: ${result.total_wages:,.2f}")
print(f"Total hours: {result.total_regular_hours + result.total_overtime_hours:,.2f}")

for emp in result.employees[:5]:
    adp = f" [ADP:{emp.adp_id}]" if emp.adp_id else ""
    print(f"  #{emp.employee_number} {emp.employee_name}{adp}")
    for shift in emp.shifts:
        print(
            f"      {shift.date_in} {shift.time_in} - {shift.time_out} "
            f"@ {shift.site_code} ({shift.regular_hours:.2f}h, "
            f"${shift.total_wages:,.2f})"
        )
```

**Arguments:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start` | `str \| date \| datetime` | Inclusive start (ISO `YYYY-MM-DD` or a date/datetime). |
| `end` | `str \| date \| datetime` | Inclusive end. |
| `site_id` | `int \| None` | Optional numeric BackOffice site id. When provided, the scraper narrows the report at the URL level (`?siteId=...`). When `None` (default), the report includes all sites. |

!!! note "`site_code` is ignored here"
    The client-level `site_code` header filter does **not** apply to
    the BackOffice path. Every shift in the returned result already
    carries its own `site_code`, so filter client-side on
    `TimesheetShift.site_code` if you need a subset, or pass an
    explicit numeric `site_id` to let the server narrow the report for
    you.

## Return types

### `BackOfficeTimeclockResult`

| Field | Type | Description |
|-------|------|-------------|
| `period_start` | `str` | ISO `YYYY-MM-DD` start of the reporting period |
| `period_end` | `str` | ISO `YYYY-MM-DD` end of the reporting period |
| `employees` | `list[EmployeeTimesheet]` | Per-employee rollups |
| `total_regular_hours` | `float` | Grand total regular hours (from the report's `Timesheet Total:` footer) |
| `total_regular_wages` | `float` | Grand total regular wages |
| `total_overtime_hours` | `float` | Grand total overtime hours |
| `total_overtime_wages` | `float` | Grand total overtime wages |
| `total_wages` | `float` | Grand total wages |

### `EmployeeTimesheet`

| Field | Type | Description |
|-------|------|-------------|
| `employee_name` | `str` | Last, First (e.g. `"Almaliki, Moustafa"`) |
| `employee_number` | `int` | The `#NNN` identifier from the report |
| `adp_id` | `str \| None` | ADP ID when the header shows `, ADP ID: NNNN` |
| `shifts` | `list[TimesheetShift]` | All shifts for this employee in the period |
| `total_regular_hours` | `float` | Employee rollup regular hours |
| `total_regular_wages` | `float` | Employee rollup regular wages |
| `total_overtime_hours` | `float \| None` | `None` when the employee is not OT-eligible (`n/a` on the report) |
| `total_overtime_wages` | `float \| None` | `None` when not OT-eligible |
| `total_wages` | `float` | Employee rollup total wages |

### `TimesheetShift`

Each row on the BackOffice report corresponds to one clock-in /
clock-out shift. Employees can have multiple shifts per day, optionally
at different sites.

| Field | Type | Description |
|-------|------|-------------|
| `date_in` | `str` | ISO `YYYY-MM-DD` clock-in date |
| `time_in` | `str` | Local time string, e.g. `"2:10 PM"` |
| `date_out` | `str` | ISO `YYYY-MM-DD` clock-out date |
| `time_out` | `str` | Local time string |
| `timezone` | `str` | Timezone abbreviation (e.g. `"CST"`) from the report |
| `site_code` | `str` | Site the shift was worked at |
| `regular_rate` | `float` | Hourly rate for regular hours (0.0 when the cell shows `$0.00`) |
| `regular_hours` | `float` | Regular hours worked |
| `regular_wages` | `float` | Regular hours × regular rate |
| `overtime_rate` | `float \| None` | `None` when `n/a` (not OT-eligible) |
| `overtime_hours` | `float \| None` | `None` when `n/a` |
| `overtime_wages` | `float \| None` | `None` when `n/a` |
| `total_wages` | `float` | Shift total wages |
| `was_modified` | `bool` | `True` for rows with the yellow "modified" warning class |
| `was_created_in_back_office` | `bool` | `True` for rows that a manager added manually from Back Office |
| `comment` | `str \| None` | Audit comment from the preceding `addon-row-comment` row (e.g. *"Unable to punch in..."*) |

## Errors

All BackOffice errors inherit from :class:`BackOfficeError` (itself a
subclass of :class:`SonnysError`).

| Exception | Raised when |
|-----------|-------------|
| `BackOfficeCredentialsError` | `backoffice_username` and/or `backoffice_password` were not supplied at client construction. The message names the missing field(s). |
| `BackOfficeLoginError` | The BackOffice login form rejected the credentials, or the login endpoint was unreachable. |
| `BackOfficeScrapeError` | The timesheets page was reached but the HTML did not match the expected structure (period header / employee blocks / `Timesheet Total:` footer). Typically indicates a BackOffice UI change. |

```python
from sonnys_data_client import (
    SonnysClient,
    BackOfficeCredentialsError,
    BackOfficeLoginError,
    BackOfficeScrapeError,
)

with SonnysClient(api_id="washu", api_key="key") as client:
    try:
        client.backoffice.timeclock("2026-03-01", "2026-03-31")
    except BackOfficeCredentialsError as e:
        print("Missing BackOffice credentials:", e)
    except BackOfficeLoginError as e:
        print("BackOffice login failed:", e)
    except BackOfficeScrapeError as e:
        print("BackOffice HTML parse failed:", e)
```

## Examples

### Monthly report with per-employee breakdown

```python
from sonnys_data_client import SonnysClient

with SonnysClient(
    api_id="washu",
    api_key="your-api-key",
    backoffice_username="your.login",
    backoffice_password="your-password",
) as client:
    result = client.backoffice.timeclock("2026-03-01", "2026-03-31")

    print(f"{result.period_start} -> {result.period_end}")
    print(f"Grand total: ${result.total_wages:,.2f} across {len(result.employees)} employees")
    print()

    top_earners = sorted(
        result.employees, key=lambda e: e.total_wages, reverse=True
    )[:10]
    for emp in top_earners:
        shifts_count = len(emp.shifts)
        sites = {s.site_code for s in emp.shifts}
        print(
            f"{emp.employee_name:<30} "
            f"${emp.total_wages:>10,.2f}   "
            f"{emp.total_regular_hours:>6.2f}h   "
            f"{shifts_count} shifts at {', '.join(sorted(sites))}"
        )
```

### Detect suspicious punches

```python
with SonnysClient(
    api_id="washu", api_key="key",
    backoffice_username="...", backoffice_password="...",
) as client:
    result = client.backoffice.timeclock("2026-03-01", "2026-03-31")

    # Modified punches and back-office-created entries are worth reviewing
    for emp in result.employees:
        for shift in emp.shifts:
            if shift.was_modified or shift.was_created_in_back_office:
                tag = "MODIFIED" if shift.was_modified else "BO-CREATED"
                print(
                    f"[{tag}] {emp.employee_name} on {shift.date_in} "
                    f"@ {shift.site_code}: {shift.comment}"
                )
```

### Filter a single-site slice client-side

```python
with SonnysClient(
    api_id="washu", api_key="key",
    backoffice_username="...", backoffice_password="...",
) as client:
    result = client.backoffice.timeclock("2026-03-01", "2026-03-31")

    joliet_shifts = [
        shift
        for emp in result.employees
        for shift in emp.shifts
        if shift.site_code == "JOLIET"
    ]
    total = sum(s.total_wages for s in joliet_shifts)
    print(f"JOLIET: {len(joliet_shifts)} shifts, ${total:,.2f}")
```

## Performance

For a mid-size operator (~80 employees, ~15 sites) over a 31-day month:

| Approach | Typical wall time | Rate-limit pressure |
|----------|-------------------|---------------------|
| `client.stats.total_labor_cost()` | several minutes (N_emp × ceil(days/14) API calls) | High — 20 req / 15 s window |
| `client.backoffice.timeclock()` | single-digit seconds (1 login + 1 report fetch) | None — BackOffice has no published limit |

The BackOffice method is usually **orders of magnitude faster** on
anything larger than a single day for a single employee. Latency scales
roughly with date range because the BackOffice renders the report
server-side, but even a full month is a single HTTP round trip.

!!! note "Session reuse"
    The BackOffice `requests.Session` is cached on the client for the
    lifetime of the `SonnysClient` instance. Subsequent `timeclock()`
    calls on the same client reuse the logged-in session (and
    transparently re-authenticate if it expires mid-session). Close the
    client — or use it as a context manager — to tear the session down.

!!! tip "Shift-level granularity is the default"
    Unlike `LaborCostResult`, which only exposes aggregate totals, the
    BackOffice result preserves **every individual shift**. This is the
    finest granularity the report exposes and is what enables per-site,
    per-day, and anomaly-detection workflows without a second round trip.
