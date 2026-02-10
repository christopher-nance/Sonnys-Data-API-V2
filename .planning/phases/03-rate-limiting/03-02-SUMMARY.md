---
phase: 03-rate-limiting
plan: 02
subsystem: rate-limiting
tags: [http-request, rate-limiting, 429-retry, exponential-backoff, time-sleep]

requires:
  - phase: 02-http-transport-errors
    provides: make_status_error, exception hierarchy, error body parsing
  - phase: 03-rate-limiting (plan 01)
    provides: RateLimiter class with acquire/reset/available
provides:
  - _request() method integrating rate limiter, error mapping, and 429 retry
  - SonnysClient constructor with max_retries parameter
affects: [05-resource-framework, 06-standard-resources, 07-account-resources, 08-transaction-resources]

tech-stack:
  added: []
  patterns: [exponential-backoff-retry, rate-limiter-integration, transport-error-mapping]

key-files:
  created: [tests/test_client.py]
  modified: [src/sonnys_data_client/_client.py]

key-decisions:
  - "Keyword-only params in _request() consistent with Phase 2 pattern"
  - "Exponential backoff base_delay=1.0 with 2**attempt (1s, 2s, 4s)"
  - "Only 429 responses trigger retry; other errors raise immediately"

patterns-established:
  - "_request() as single HTTP pipeline: rate-limit → send → error-map → retry"
  - "Mock session.request + mock time.sleep for deterministic client tests"

issues-created: []

duration: 4min
completed: 2026-02-10
---

# Phase 3 Plan 2: HTTP Request Method with Rate Limiting and 429 Retry Summary

**`_request()` pipeline integrating sliding window rate limiter, transport error mapping, and exponential backoff 429 retry (1s/2s/4s)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T15:37:17Z
- **Completed:** 2026-02-10T15:41:28Z
- **Tasks:** 1 (TDD: RED/GREEN/REFACTOR)
- **Files modified:** 2

## Accomplishments
- `_request(method, path, *, params)` method as single HTTP pipeline for all API calls
- Rate limiter integration: `acquire()` check before every request, `sleep(wait)` when throttled
- Transport error mapping: `requests.ConnectionError` → `APIConnectionError`, `requests.Timeout` → `APITimeoutError`
- 429 retry with exponential backoff (1s, 2s, 4s) up to `max_retries` (default 3)
- Non-429 errors raise immediately via `make_status_error(response)`
- 12 new tests covering success, params, transport errors, status errors, retry, and rate limiter integration

## Task Commits

TDD cycle commits:

1. **RED: Failing tests** - `a1359e7` (test)
2. **GREEN: Implementation** - `b4ccbba` (feat)
3. **REFACTOR: Cleanup** - not needed (implementation was clean and minimal)

**Plan metadata:** (see final commit)

## Files Created/Modified
- `tests/test_client.py` - 12 tests for _request: success, params, transport errors, status errors, 429 retry, rate limiter
- `src/sonnys_data_client/_client.py` - Added imports, max_retries param, _rate_limiter instance, _request() method

## Decisions Made
- Keyword-only `params` in `_request()` — consistent with Phase 2 pattern
- Exponential backoff with `base_delay=1.0 * (2 ** attempt)` — 1s, 2s, 4s delays
- Only 429 responses trigger retry; all other errors raise immediately (no retry on 5xx)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Phase 3 complete: rate limiting fully operational
- `_request()` is the single HTTP pipeline all resource methods will call
- Ready for Phase 4: Response Models (Pydantic v2 models for API response types)

---
*Phase: 03-rate-limiting*
*Completed: 2026-02-10*
