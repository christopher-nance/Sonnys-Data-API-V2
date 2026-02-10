---
phase: 02-http-transport-errors
plan: 01
subsystem: api
tags: [python, exceptions, error-handling, http-errors]

# Dependency graph
requires:
  - phase: 01-project-foundation
    provides: Package scaffolding, __init__.py public API surface
provides:
  - 8-class exception hierarchy for typed error handling
  - Two-branch tree: APIConnectionError (network) and APIStatusError (HTTP)
  - error_type field for Sonny's API sub-type discrimination
affects: [02-http-transport-errors, 03-rate-limiting, 05-resource-framework]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-branch-exception-tree, keyword-only-args-for-status-errors]

key-files:
  created:
    - src/sonnys_data_client/_exceptions.py
  modified:
    - src/sonnys_data_client/__init__.py

key-decisions:
  - "Keyword-only args for APIStatusError (status_code, body, error_type) — prevents positional arg mistakes"
  - "Default messages on connection errors — callers get useful messages without specifying"

patterns-established:
  - "Two-branch exception tree: APIConnectionError for transport, APIStatusError for HTTP responses"
  - "error_type field on APIStatusError for Sonny's API type string discrimination"

issues-created: []

# Metrics
duration: 1min
completed: 2026-02-10
---

# Phase 2 Plan 1: Exception Hierarchy Summary

**Two-branch exception tree with 8 typed classes — APIConnectionError for network failures, APIStatusError with status_code/body/error_type for HTTP errors**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-10T08:54:28Z
- **Completed:** 2026-02-10T08:55:29Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Complete exception hierarchy: SonnysError → APIError → two branches (connection vs status)
- APIStatusError stores status_code, body, and error_type for full error context
- All 8 exception classes exported from top-level package
- Ruff lint clean, all verification checks pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create exception hierarchy module** - `b614606` (feat)
2. **Task 2: Export exception classes from public API** - `6e6765c` (feat)

## Files Created/Modified
- `src/sonnys_data_client/_exceptions.py` - 8 exception classes with two-branch hierarchy
- `src/sonnys_data_client/__init__.py` - Added all exception imports and __all__ entries

## Decisions Made
- Keyword-only args for APIStatusError (status_code, body, error_type) — prevents positional arg mistakes
- Default messages on APIConnectionError and APITimeoutError — useful defaults without requiring message arg

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Exception hierarchy complete, ready for Plan 02-02 to add error mapping from HTTP responses
- APIStatusError.error_type field ready for Sonny's API type string mapping
- No blockers

---
*Phase: 02-http-transport-errors*
*Completed: 2026-02-10*
