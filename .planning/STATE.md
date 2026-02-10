# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** Dead-simple interface with rock-solid reliability — any developer or AI agent picks it up instantly, and it never crashes your apps.
**Current focus:** Phase 8 in progress — Transaction Resources (v1 list/get/by-type done, v2 next)

## Current Position

Phase: 8 of 10 (Transaction Resources)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-10 — Completed 08-01-PLAN.md

Progress: ████████░░ 82%

## Performance Metrics

**Velocity:**
- Total plans completed: 14
- Average duration: 2.9 min
- Total execution time: 0.66 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Project Foundation | 1/1 | 4 min | 4 min |
| 2. HTTP Transport & Errors | 2/2 | 5 min | 2.5 min |
| 3. Rate Limiting | 2/2 | 7 min | 3.5 min |
| 4. Response Models | 3/3 | 9 min | 3 min |
| 5. Resource Framework | 1/1 | 4 min | 4 min |
| 6. Standard Resources | 2/2 | 5 min | 2.5 min |
| 7. Account Resources | 2/2 | 4 min | 2 min |
| 8. Transaction Resources | 1/2 | 2 min | 2 min |

**Recent Trend:**
- Last 5 plans: 3 min, 2 min, 2 min, 2 min, 2 min
- Trend: —

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 01 | PEP 639 SPDX license format | Forward-compatible with latest PyPA standards |
| 01 | Python 3.10+ native type syntax | No typing module imports needed |
| 01 | Underscore-prefixed internals | Public API exposed only via __init__.py |
| 02 | Keyword-only args for APIStatusError | Prevents positional arg mistakes |
| 02 | Default messages on connection errors | Useful defaults without requiring message arg |
| 02 | 5xx fallback to ServerError | Server errors should always be ServerError, not base APIStatusError |
| 02 | messages array joined with "; " | PayloadValidationError readable single string |
| 03 | time.monotonic over time.time | Immune to system clock changes and NTP adjustments |
| 03 | acquire() returns wait duration, does not sleep | Keeps rate limiter pure and testable; caller decides |
| 03 | Exponential backoff 1s/2s/4s for 429 retry | Standard doubling from base_delay=1.0 |
| 03 | Only 429 triggers retry; other errors raise immediately | No retry on 5xx — fail fast for non-transient errors |
| 04 | SonnysModel with ConfigDict(populate_by_name, alias_generator=to_camel) | Automatic snake_case-to-camelCase JSON aliasing |
| 04 | TransactionV2ListItem extends TransactionListItem; TransactionJobItem extends Transaction | Inheritance for shared fields between v1/v2/job variants |
| 04 | Field(alias="lastFourCC") for RecurringBilling | to_camel produces wrong casing for abbreviations |
| 04 | alias_generator=None for RecurringStatusChange | API returns snake_case for this endpoint |
| 04 | Shared sub-objects in _washbooks.py imported by _recurring.py | Avoids duplication; WashbookTag/Vehicle/Customer reused |
| 04 | Field(alias="siteID") for Site.site_id | to_camel produces "siteId" but API returns "siteID" |
| 04 | 30 models total in types/__all__ | Plan said 29 but actual count includes TransactionJobItem |
| 05 | ListableResource/GettableResource as independent mixins | Concrete resources inherit one or both |
| 05 | TYPE_CHECKING guard for circular imports | _resources.py imports SonnysClient only at type-check time |
| 05 | _list_paginated/_list_non_paginated private dispatch | Clean separation of paginated vs non-paginated logic |
| 06 | Module-level resource imports in _client.py | No circular dependency — resources import from _resources.py not _client.py |
| 06 | functools.cached_property for resource accessors | Instantiated once per client, no repeated allocation |
| 06 | get_clock_entries flattens weeks[].clockEntries[] | Keeps consumer API simple — flat list[ClockEntry] |
| 06 | Sites _path="/site/list" with _paginated=False | Non-standard API endpoint returns all sites at once |
| 07 | Giftcards _path="/giftcard-liablilty" (API typo) | API misspells "liability" — must match exactly |
| 07 | Washbooks _items_key="accounts" | API returns "accounts" not "washbooks" in response |
| 07 | RecurringAccounts class name (not Recurring) | Avoids collision with Recurring Pydantic model |
| 07 | _paginated_fetch private helper for custom endpoints | DRYs up offset/limit/total pagination across 3 methods |

### Deferred Issues

None yet.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-10T18:16:25Z
Stopped at: Completed 08-01-PLAN.md — Phase 8 in progress
Resume file: None
