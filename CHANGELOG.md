# Changelog

All notable changes to `sonnys-data-client` are documented in this file.

## 1.4.1

### Fixed

- `client.backoffice.timeclock()` no longer raises
  ``BackOfficeScrapeError`` when the requested date range has zero
  clock entries. BackOffice renders a single "No clock entries found
  matching the given criteria." sentinel in that case; the scraper
  now detects it and returns an empty
  :class:`BackOfficeTimeclockResult` (empty ``employees`` list, all
  totals ``0.0``, ``period_start`` / ``period_end`` echo the caller's
  requested range).

## 1.4.0

### Added

- **BackOffice scraper (`client.backoffice.timeclock()`).** A new
  resource that logs in to the Sonny's BackOffice web UI and scrapes
  the `/report/employee-timesheets` page for per-shift, per-employee
  timeclock data. On multi-site operators this is orders of magnitude
  faster than `client.stats.total_labor_cost()` because the report
  renders every employee across every site in a single HTTP round
  trip, with no published rate limit to contend with.
- New init parameters: `backoffice_username` and `backoffice_password`
  (both keyword-only, both optional). The existing `api_id` doubles as
  the BackOffice subdomain, so no new subdomain parameter is needed.
- New response models: `TimesheetShift`, `EmployeeTimesheet`,
  `BackOfficeTimeclockResult` (exposed from the top-level package).
- `TimesheetShift.is_open` property — `True` when the employee was
  still on the clock at the moment the report was rendered
  (`date_out` / `time_out` are `None` for open shifts). Partial
  hours and wages accumulated so far are still populated and rolled
  up into the employee and period totals.
- New exception classes: `BackOfficeError`, `BackOfficeCredentialsError`,
  `BackOfficeLoginError`, `BackOfficeScrapeError` (all inherit from
  `SonnysError`).
- `beautifulsoup4` added to core dependencies (~1MB, no native deps).
- Full docs guide at `docs/guides/backoffice.md` covering credentials,
  method signature, return types, open shifts, errors, and performance.

### Fixed

- `tests/test_client.py::test_429_backoff_timing` updated to match the
  2s/4s/6s retry delays introduced in 1.3.1 (the test was still
  asserting the old 1s/2s/4s values).

### Backwards compatibility

- All existing `SonnysClient(api_id, api_key, ...)` call sites
  continue to work without changes. Any attempt to call a BackOffice
  method on a client that was constructed without BackOffice
  credentials raises `BackOfficeCredentialsError` with a message
  naming the missing field(s).
