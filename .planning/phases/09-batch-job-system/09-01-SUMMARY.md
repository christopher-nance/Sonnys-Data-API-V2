---
phase: 09-batch-job-system
plan: 01
subsystem: api
tags: [batch-job, polling, transactions, time.monotonic, asyncjob]

# Dependency graph
requires:
  - phase: 05-resource-framework
    provides: Resource mixin pattern, _request pipeline
  - phase: 08-transaction-resources
    provides: Transactions class, TransactionJobItem model, _paginated_fetch
provides:
  - "load_job() method on Transactions — submit/poll/return batch job flow"
  - "Auto-polling with configurable interval and timeout"
  - "Status-driven control flow: pass/working/fail"
affects: [10-packaging-distribution]

# Tech tracking
tech-stack:
  added: []
  patterns: ["submit-poll-return async job pattern with deadline-based timeout"]

key-files:
  created: [tests/test_batch_job.py]
  modified: [src/sonnys_data_client/resources/_transactions.py]

key-decisions:
  - "APIError for job failure, APITimeoutError for deadline — no new exception classes"
  - "Check timeout AFTER poll attempt, not before sleep — ensures at least one poll"
  - "Default poll_interval=2.0s, timeout=300.0s"

patterns-established:
  - "Submit-poll-return: POST job → extract hash → poll GET with hash → status switch"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 9 Plan 1: Batch Job Load and Poll Summary

**Submit-poll-return batch job flow on Transactions with status-driven polling, configurable timeout, and 15 test scenarios**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T18:32:56Z
- **Completed:** 2026-02-10T18:36:56Z
- **Tasks:** 2 (RED + GREEN; no REFACTOR needed)
- **Files modified:** 2

## Accomplishments

- `load_job()` method on Transactions: POST to `/transaction/load-job`, poll `/transaction/get-job-data` until pass/fail/timeout
- Status-driven control flow: "pass" returns parsed `list[TransactionJobItem]`, "fail" raises `APIError`, "working" sleeps and retries
- Deadline-based timeout using `time.monotonic()` — raises `APITimeoutError` when exceeded
- 15 comprehensive tests covering all poll scenarios with deterministic time mocking

## TDD Cycle

### RED - Failing Tests

Created `tests/test_batch_job.py` with 15 tests across 6 test classes:
- `TestLoadJobSubmit` (2 tests) — POST endpoint and hash extraction
- `TestLoadJobImmediatePass` (1 test) — immediate status="pass"
- `TestLoadJobWorkingThenPass` (2 tests) — working→pass with sleep
- `TestLoadJobFailure` (2 tests) — immediate fail, working→fail
- `TestLoadJobTimeout` (2 tests) — single poll timeout, multi-poll timeout
- `TestLoadJobDataParsing` (2 tests) — multi-item parsing, empty data
- `TestLoadJobConfiguration` (4 tests) — custom poll_interval, custom timeout, default values

All 15 tests failed as expected (AttributeError: Transactions has no `load_job`).

### GREEN - Implementation

Added `load_job()` to `Transactions` class (~30 lines):
1. POST to `/transaction/load-job` with `**params`
2. Extract hash from `response.json()["data"]["hash"]`
3. Poll loop with `time.monotonic()` deadline
4. Status switch: "pass" → return parsed list, "fail" → raise APIError, "working" → check deadline → sleep

All 15 tests passed on first run. Full suite (110 tests) also green.

### REFACTOR

No refactoring needed — implementation is already concise (~20 lines of logic), follows established patterns, and reads cleanly.

## Task Commits

1. **RED: Failing tests** - `534e9c9` (test)
2. **GREEN: Implementation** - `61cecf4` (feat)

## Files Created/Modified

- `tests/test_batch_job.py` - 15 tests for batch job submit-poll-return flow (created)
- `src/sonnys_data_client/resources/_transactions.py` - Added `load_job()` method with imports (modified)

## Decisions Made

- Used existing `APIError`/`APITimeoutError` instead of new exception classes — semantically correct, avoids over-engineering for single method
- Check timeout AFTER poll attempt (not before sleep) — ensures at least one poll even with timeout=0
- Default poll_interval=2.0s to avoid rate limiter starvation (per research recommendation)
- Default timeout=300.0s (5 min) — generous for batch jobs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 9 complete — Batch Job System fully implemented
- All transaction patterns covered: list, by-type, detail, v2, batch job
- Ready for Phase 10: Packaging & Distribution

---
*Phase: 09-batch-job-system*
*Completed: 2026-02-10*
