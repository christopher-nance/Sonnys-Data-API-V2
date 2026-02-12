# Phase 27: Labor Data Layer - Research

**Researched:** 2026-02-12
**Domain:** Sonny's API employee clock entries — bulk aggregation
**Confidence:** HIGH

<research_summary>
## Summary

Researched how to bulk-fetch employee clock entries from the Sonny's API for labor cost computation. The existing `Employees` resource provides `get_clock_entries(employee_id, start_date, end_date)` which returns a flat list of `ClockEntry` objects, each with `regular_hours`, `regular_rate`, `overtime_hours`, `overtime_rate`, and `site_code`.

Two critical constraints discovered:
1. **14-day max date range** per clock entries request — a full month requires 3 API calls per employee
2. **EmployeeListItem has no `active` flag** — filtering active employees requires either N additional `get()` calls or a "fetch-all, filter by entries" approach

The recommended pattern mirrors the existing Stats resource: bulk-fetch, then aggregate locally. The main challenge is rate limiting — for 50 employees over 31 days: 1 list + 150 clock entry calls = ~151 API calls (~2 minutes at 20 req/15s).

**Primary recommendation:** Add a `_fetch_all_clock_entries(start, end)` method to StatsResource that chunks date ranges into 14-day windows, iterates all employees, and returns aggregated entries — filtering by `site_code` locally.
</research_summary>

<api_contract>
## API Contract: Clock Entries Endpoint

**Endpoint:** `GET /employee/{employee_id}/clock-entries`

**Parameters:**
- `employee_id` (path, required) — employee ID
- `startDate` (query, optional) — ISO date string YYYY-MM-DD
- `endDate` (query, optional) — ISO date string YYYY-MM-DD

**Constraint:** Date range max 14 days. Exceeding returns validation error.

**Response structure (nested weeks):**
```json
{
  "data": {
    "weeks": [
      {
        "week": "2021-01-08 - 2021-01-14",
        "weekTotalRegularHours": 40.5,
        "weekTotalOverTimeHours": 2.0,
        "clockEntries": [
          {
            "clockIn": "2020-05-19T00:01:02.000Z",
            "clockOut": "2020-05-19T08:30:00.000Z",
            "regularRate": 5.4,
            "regularHours": 5.4,
            "overtimeEligible": false,
            "overtimeRate": 5.4,
            "overtimeHours": 2.0,
            "wasModified": false,
            "modificationTimestamp": null,
            "wasCreatedInBackOffice": false,
            "siteCode": "JOLIET"
          }
        ]
      }
    ]
  }
}
```

**Flattening:** Current implementation loops `data.weeks[].clockEntries[]` and validates each as `ClockEntry`.

**No pagination:** All entries for the date range returned in one response.

**No site_code query param:** Filtering must happen locally on `ClockEntry.site_code`.
</api_contract>

<existing_patterns>
## Existing Codebase Patterns

### Employee Resource (`_employees.py`)
```python
def get_clock_entries(
    self, employee_id, *, start_date=None, end_date=None
) -> list[ClockEntry]:
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date:   params["endDate"]   = end_date
    response = self._client._request("GET", f"/employee/{employee_id}/clock-entries", params=params)
    data = response.json()["data"]
    entries = []
    for week in data["weeks"]:
        for entry in week["clockEntries"]:
            entries.append(ClockEntry.model_validate(entry))
    return entries
```

- Date params are plain strings — NOT Unix timestamps like Stats
- No timezone conversion needed (API handles it)

### Stats Resource Pattern (`_stats.py`)
```python
# Bulk fetch → local aggregation
transactions = self._fetch_transactions_v2(start, end)  # 1 API call
plan_sale_ids = {t.trans_id for t in txns if t.is_recurring_plan_sale}  # local filter
for txn_id in plan_sale_ids:
    detail = self._client.transactions.get(txn_id)  # N verification calls
```

### Employee Models
- `EmployeeListItem`: `employee_id`, `first_name`, `last_name` — **NO `active` flag**
- `Employee` (from get()): adds `active`, `start_date`, `phone`, `email`
- `ClockEntry`: `regular_hours`, `regular_rate`, `overtime_hours`, `overtime_rate`, `site_code`

### Rate Limiter
- 20 requests / 15-second sliding window
- Built-in 429 retry with exponential backoff (1s, 2s, 4s)
- Max 3 retries
</existing_patterns>

<implementation_constraints>
## Implementation Constraints

### 14-Day Date Range Chunking

A 31-day month requires 3 chunks per employee:
```
Chunk 1: Jan 01 → Jan 14 (14 days)
Chunk 2: Jan 15 → Jan 28 (14 days)
Chunk 3: Jan 29 → Jan 31 (3 days)
```

General formula: `ceil(days / 14)` chunks per employee.

### Active Employee Filtering

`EmployeeListItem` (from `list()`) lacks the `active` flag. Options:

| Approach | Extra API Calls | Recommendation |
|----------|:---------------:|:--------------:|
| Call `get()` per employee to check `active` | +N calls | No — doubles cost |
| Fetch clock entries for all, skip empties | 0 | **Yes** — simple, effective |
| Cache active employee list | 0 (after first run) | Not in scope (no caching layer) |

**Recommendation:** Fetch for all employees. Employees with zero entries naturally excluded from labor cost aggregation. Inactive employees without shifts produce zero cost.

### Rate Limit Budget

| Scenario | Employees | Chunks/Employee | Total Calls | Time @ 20req/15s |
|----------|:---------:|:---------------:|:-----------:|:-----------------:|
| Small site, 1 week | 20 | 1 | 21 | ~16s |
| Small site, 1 month | 20 | 3 | 61 | ~46s |
| Medium site, 1 month | 50 | 3 | 151 | ~113s |
| Large site, 1 month | 100 | 3 | 301 | ~226s |

Note: Stats `report()` already uses 3 + ~N calls (~18 for a single day). Labor data is inherently more expensive because clock entries have no bulk endpoint across employees.

### Site Code Filtering

- Filter locally: `[e for e in entries if e.site_code == self._client.site_code]`
- The `SonnysClient.site_code` already scopes all requests
- Clock entries for employees at other sites will have different `site_code` values
- Multi-site employees may have entries at different sites — filter by site
</implementation_constraints>

<architecture>
## Recommended Architecture

### New Method on StatsResource

```python
def _fetch_all_clock_entries(
    self,
    start: str | datetime,
    end: str | datetime,
) -> list[ClockEntry]:
    """Fetch clock entries for all employees, chunking by 14-day windows.

    Filters by client's site_code if set.

    API cost: 1 + (N_employees × ceil(days/14)) calls
    """
    # 1. Get all employees (1+ API calls, paginated)
    employees = self._client.employees.list()

    # 2. Build 14-day date chunks
    chunks = self._build_date_chunks(start, end, max_days=14)

    # 3. Fetch clock entries per employee per chunk
    all_entries: list[ClockEntry] = []
    for emp in employees:
        for chunk_start, chunk_end in chunks:
            entries = self._client.employees.get_clock_entries(
                emp.employee_id,
                start_date=chunk_start,
                end_date=chunk_end,
            )
            all_entries.extend(entries)

    # 4. Filter by site_code locally
    site = self._client.site_code
    if site:
        all_entries = [e for e in all_entries if e.site_code == site]

    return all_entries
```

### Date Chunking Helper

```python
def _build_date_chunks(
    self,
    start: str | datetime,
    end: str | datetime,
    max_days: int = 14,
) -> list[tuple[str, str]]:
    """Split a date range into max_days-sized chunks.

    Returns list of (start_date, end_date) string pairs in YYYY-MM-DD format.
    """
    ...
```

### Integration with report()

```python
def report(self, start, end) -> StatsReport:
    # Existing: 3 bulk + ~N detail calls
    transactions_v2 = self._fetch_transactions_v2(start, end)
    wash_txns = self._fetch_wash_transactions(start, end)
    recurring_txns = self._fetch_recurring_transactions(start, end)

    # New: 1 + (employees × chunks) calls
    clock_entries = self._fetch_all_clock_entries(start, end)

    # Compute all KPIs locally
    ...
```
</architecture>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Exceeding 14-Day Limit
**What goes wrong:** API returns validation error for date ranges > 14 days
**Why it happens:** Clock entries endpoint enforces hard 14-day max
**How to avoid:** Always chunk date ranges before calling the API
**Warning signs:** `ValidationError` from API on date range requests

### Pitfall 2: Double-Counting Multi-Site Employees
**What goes wrong:** Employee works at JOLIET and PLAINFIELD — both sites' entries included
**Why it happens:** Clock entries return all sites, not just the authenticated site
**How to avoid:** Filter by `site_code` matching `client.site_code` after fetching
**Warning signs:** Labor cost higher than expected, entries from unexpected sites

### Pitfall 3: Assuming Active Filtering Is Free
**What goes wrong:** Adding `get()` calls to check `active` flag doubles API cost
**Why it happens:** `EmployeeListItem` doesn't include `active` field
**How to avoid:** Skip active filtering — employees with no clock entries contribute zero cost
**Warning signs:** Unexpectedly high API call count, slow execution

### Pitfall 4: Rate Limit Exhaustion with Large Teams
**What goes wrong:** 429 errors cascade during bulk fetch
**Why it happens:** 301 calls for 100 employees × 3 chunks overwhelms rate limit
**How to avoid:** Let built-in rate limiter + backoff handle it; document expected timing
**Warning signs:** Many 429 retries in logs, execution taking 5+ minutes
</common_pitfalls>

<open_questions>
## Open Questions

1. **Does the API return entries for employees at ALL sites, or only the authenticated site?**
   - What we know: `ClockEntry.site_code` exists; `X-Sonnys-Site-Code` header is auth-scoped
   - What's unclear: Whether the header filters clock entry responses or just authorizes access
   - Recommendation: Test with JOLIET site code, check if entries from other sites appear
   - Impact: If header doesn't filter, local filtering is mandatory

2. **What happens when an employee has no clock entries for a date range?**
   - What we know: API returns nested `weeks[]` structure
   - What's unclear: Does it return empty `weeks: []` or an error?
   - Recommendation: Handle both — empty list means zero entries
   - Impact: Low — just need graceful empty handling

3. **Date format edge case: does the API use inclusive or exclusive end dates?**
   - What we know: Parameters are `startDate` and `endDate` as YYYY-MM-DD strings
   - What's unclear: Is Jan 14 endDate inclusive (includes Jan 14 entries)?
   - Recommendation: Test boundary — matters for chunking to avoid gaps/overlaps
   - Impact: Could miss or double-count a day of entries at chunk boundaries
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `src/sonnys_data_client/resources/_employees.py` — current get_clock_entries() implementation
- `src/sonnys_data_client/types/_employees.py` — ClockEntry, EmployeeListItem models
- `src/sonnys_data_client/resources/_stats.py` — bulk fetch + local aggregation pattern
- `bo-data-open-api.yml` — API contract: 14-day max range, response structure, parameters

### Secondary (MEDIUM confidence)
- `docs/guides/employees.md` — usage examples with YYYY-MM-DD date format
- `.planning/phases/06-standard-resources/06-02-PLAN.md` — employee resource design decisions

### Tertiary (LOW confidence - needs validation)
- Site-code filtering behavior on clock entries (needs live testing)
- End date inclusivity (needs live testing)
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Sonny's API employee/clock-entries endpoint
- Ecosystem: Existing SDK patterns (rate limiter, pagination, date utils)
- Patterns: Bulk data fetching, date chunking, local aggregation
- Pitfalls: 14-day limit, active filtering, multi-site entries, rate limits

**Confidence breakdown:**
- API contract: HIGH — verified against OpenAPI spec
- Existing patterns: HIGH — read from source code
- Architecture: HIGH — mirrors established Stats resource pattern
- Pitfalls: HIGH — derived from API constraints + codebase analysis
- Open questions: MEDIUM — need live API testing to resolve

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days — internal API, stable)
</metadata>

---

*Phase: 27-labor-data-layer*
*Research completed: 2026-02-12*
*Ready for planning: yes*
