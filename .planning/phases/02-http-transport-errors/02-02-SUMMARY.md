---
phase: 02-http-transport-errors
plan: 02
subsystem: api
tags: [requests, error-parsing, status-codes, tdd, pytest]

# Dependency graph
requires:
  - phase: 02-http-transport-errors/01
    provides: Exception hierarchy (APIStatusError, AuthError, RateLimitError, etc.)
provides:
  - parse_error_body() for extracting structured error info from HTTP responses
  - make_status_error() for mapping status codes to typed exceptions
  - _STATUS_MAP for status-code-to-exception-class lookup
affects: [http-transport, rate-limiting, resource-framework]

# Tech tracking
tech-stack:
  added: []
  patterns: [status-code dispatch with 5xx fallback, defensive JSON parsing]

key-files:
  created: [tests/test_exceptions.py]
  modified: [src/sonnys_data_client/_exceptions.py]

key-decisions:
  - "5xx fallback to ServerError when status not in _STATUS_MAP"
  - "messages array joined with '; ' for PayloadValidationError"
  - "Empty body produces 'HTTP {status_code}' as default message"

patterns-established:
  - "Mock responses via requests.models.Response with _content injection for testing"
  - "Module-level functions (not class methods) for testability"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 2 Plan 2: Error Body Parsing & Status Mapping Summary

**TDD-driven `parse_error_body()` and `make_status_error()` covering 13 Sonny's error types across 5 status codes with JSON/non-JSON/empty body edge cases**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T09:01:47Z
- **Completed:** 2026-02-10T09:05:33Z
- **TDD Phases:** RED, GREEN (no REFACTOR needed)
- **Tests:** 17 passing
- **Files modified:** 2

## Accomplishments
- 17 comprehensive test cases covering all error parsing paths and status code mappings
- `parse_error_body()` handles JSON dict, non-dict JSON, HTML, and empty bodies gracefully
- `make_status_error()` maps 400/403/404/422/429/500 to typed exceptions with 5xx fallback to ServerError
- PayloadValidationError `messages` array properly joined with "; " separator
- All exception attributes (message, status_code, body, error_type) preserved correctly

## TDD Cycle

### RED - Failing Tests
- Created `tests/test_exceptions.py` with 17 test cases in two classes
- `TestParseErrorBody` (5 tests): JSON dict, JSON string, JSON array, HTML body, empty body
- `TestMakeStatusError` (12 tests): All status codes, edge cases, HTML/empty bodies
- Tests failed with ImportError (functions didn't exist yet)

### GREEN - Implementation
- Added `_STATUS_MAP` dict mapping 6 status codes to exception classes
- Implemented `parse_error_body()` with try/except JSON parsing and fallbacks
- Implemented `make_status_error()` with status dispatch, message extraction, and 5xx fallback
- All 17 tests passed on first run

### REFACTOR
- Not needed — implementation was clean and minimal

## Task Commits

Each TDD phase was committed atomically:

1. **RED: Failing tests** - `af79202` (test)
2. **GREEN: Implementation** - `a6ad0df` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `tests/test_exceptions.py` - 17 test cases for parse_error_body and make_status_error
- `src/sonnys_data_client/_exceptions.py` - Added _STATUS_MAP, parse_error_body(), make_status_error()

## Decisions Made
- 5xx status codes not in _STATUS_MAP default to ServerError (not APIStatusError) — server errors should always be ServerError
- PayloadValidationError `messages` array joined with "; " — readable single string for the exception message
- Empty body produces "HTTP {status_code}" as fallback message — always a useful default

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness
- Error parsing and mapping complete — ready for HTTP request/response cycle integration
- Phase 2 complete — all exception infrastructure in place for Phase 3 (Rate Limiting)

---
*Phase: 02-http-transport-errors*
*Completed: 2026-02-10*
