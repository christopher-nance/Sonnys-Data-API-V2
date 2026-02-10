---
phase: 05-resource-framework
plan: 01
subsystem: api
tags: [resources, pagination, pydantic, mixin]

# Dependency graph
requires:
  - phase: 02-http-transport-errors
    provides: _request() HTTP pipeline
  - phase: 04-response-models
    provides: SonnysModel base class and all 30 Pydantic models
provides:
  - BaseResource class with _client reference
  - ListableResource with auto-pagination loop (offset=1, increment by limit)
  - GettableResource with detail path template substitution
  - Non-paginated list support via _paginated=False
affects: [06-standard-resources, 07-account-resources, 08-transaction-resources]

# Tech tracking
tech-stack:
  added: []
  patterns: [mixin-based resource classes, TYPE_CHECKING guard for circular imports, paginated vs non-paginated dispatch]

key-files:
  created: [src/sonnys_data_client/_resources.py, tests/test_resources.py]
  modified: []

key-decisions:
  - "ListableResource/GettableResource as independent mixins — concrete resources inherit one or both"
  - "TYPE_CHECKING guard to avoid circular import between _resources.py and _client.py"
  - "_list_paginated/_list_non_paginated private dispatch for clean separation"

patterns-established:
  - "Resource mixin pattern: subclass sets class attrs (_path, _items_key, _model), inherits list()/get()"
  - "model_validate() for Pydantic v2 alias-aware parsing"
  - "Non-paginated flag: _paginated=False skips offset/limit params"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 5 Plan 1: Base Resource Classes Summary

**BaseResource/ListableResource/GettableResource mixin hierarchy with auto-pagination loop (offset=1, limit-increment) and non-paginated dispatch, tested with 9 cases covering multi-page, single-page, empty, non-paginated, extra params, detail get, and combined resource**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T17:19:20Z
- **Completed:** 2026-02-10T17:23:38Z
- **Tasks:** 1 (TDD feature: RED/GREEN/REFACTOR)
- **Files modified:** 2

## Accomplishments
- BaseResource stores `_client` reference via `__init__` with TYPE_CHECKING guard
- ListableResource with auto-pagination: offset starts at 1, increments by `_default_limit`, stops when `offset > total`
- Non-paginated list via `_paginated=False` — single request, no offset/limit params
- GettableResource with `{id}` path template substitution and `data` envelope parsing
- 9 tests covering all 7 planned behaviors plus 2 bonus cases (non-paginated extra params, combined resource)

## TDD Cycle

### RED - Failing Tests
- Created `tests/test_resources.py` with 9 tests across 4 test classes
- Test-only models: `DummyListItem`, `DummyDetail` inheriting SonnysModel
- Test-only resources: `PaginatedResource`, `NonPaginatedResource`, `DetailResource`, `ComplexPathResource`, `FullResource`
- Helper: `_make_response()` builds `requests.Response` with `_content` injection
- Failed with `ModuleNotFoundError: No module named 'sonnys_data_client._resources'`
- Commit: `41fb19d`

### GREEN - Implementation
- Created `src/sonnys_data_client/_resources.py` (126 lines)
- `BaseResource.__init__(client)` with TYPE_CHECKING import for SonnysClient
- `ListableResource.list(**params)` dispatches to `_list_paginated` or `_list_non_paginated`
- `GettableResource.get(id)` replaces `{id}` in `_detail_path`, parses `response.json()["data"]`
- All 9 tests pass
- Commit: `64ac7f9`

### REFACTOR - Cleanup
- Removed unused `call` import from `unittest.mock` and unused `BaseResource` import from test file
- All 9 tests still pass
- Commit: `74ce332`

## Task Commits

1. **RED: Failing tests for base resource classes** - `41fb19d` (test)
2. **GREEN: Implement base resource classes** - `64ac7f9` (feat)
3. **REFACTOR: Remove unused imports** - `74ce332` (refactor)

## Files Created/Modified
- `src/sonnys_data_client/_resources.py` - BaseResource, ListableResource, GettableResource (126 lines)
- `tests/test_resources.py` - 9 tests with test-only models and helpers (379 lines)

## Decisions Made
- ListableResource and GettableResource as independent mixins — concrete resources inherit one or both (Items → ListableResource only, Customers → both)
- TYPE_CHECKING guard to avoid circular import between `_resources.py` and `_client.py`
- Private dispatch methods `_list_paginated`/`_list_non_paginated` for clean separation of concerns

## Deviations from Plan

None - plan executed exactly as written.

Two bonus tests added beyond the 7 planned: `test_non_paginated_with_extra_params` and `test_full_resource_can_list_and_get`. These strengthen coverage without scope creep.

## Issues Encountered

None

## Next Phase Readiness
- Resource framework complete — BaseResource, ListableResource, GettableResource ready for inheritance
- Phase 6 (Standard Resources) can begin: Customers, Items, Employees, Sites
- All class attributes documented in docstrings for easy subclass implementation
- Phase 5 complete (single plan phase)

---
*Phase: 05-resource-framework*
*Completed: 2026-02-10*
