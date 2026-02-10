---
phase: 06-standard-resources
plan: 01
subsystem: api
tags: [resources, customers, items, cached-property, mixins]

# Dependency graph
requires:
  - phase: 05-resource-framework
    provides: ListableResource/GettableResource base classes, auto-pagination
  - phase: 04-response-models
    provides: CustomerListItem, Customer, Item Pydantic models
provides:
  - Customers resource class (list + detail)
  - Items resource class (list only)
  - SonnysClient.customers and SonnysClient.items properties
affects: [07-account-resources, 08-transaction-resources]

# Tech tracking
tech-stack:
  added: []
  patterns: [functools.cached_property for lazy resource instantiation]

key-files:
  created:
    - src/sonnys_data_client/resources/_customers.py
    - src/sonnys_data_client/resources/_items.py
  modified:
    - src/sonnys_data_client/resources/__init__.py
    - src/sonnys_data_client/_client.py
    - src/sonnys_data_client/__init__.py

key-decisions:
  - "Module-level imports for resources in _client.py — no circular dependency since resources import from _resources.py not _client.py"
  - "functools.cached_property for resource accessors — instantiated once per client, no repeated allocation"

patterns-established:
  - "Resource wiring pattern: cached_property on SonnysClient, module-level import, export from resources/__init__.py and package __init__.py"

issues-created: []

# Metrics
duration: 3 min
completed: 2026-02-10
---

# Phase 6 Plan 1: Customers and Items Resources Summary

**Customers (list+get) and Items (list) resource classes wired into SonnysClient via cached_property accessors**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-10T17:32:32Z
- **Completed:** 2026-02-10T17:35:01Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Customers resource class with list and get via ListableResource + GettableResource mixins
- Items resource class with list via ListableResource mixin
- SonnysClient.customers and SonnysClient.items as cached_property accessors
- All 95 existing tests pass, zero lint errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Customers and Items resource classes** - `9352e24` (feat)
2. **Task 2: Wire Customers and Items into SonnysClient** - `dd130d7` (feat)

## Files Created/Modified
- `src/sonnys_data_client/resources/_customers.py` - Customers resource (list + detail via dual mixin inheritance)
- `src/sonnys_data_client/resources/_items.py` - Items resource (list only via ListableResource)
- `src/sonnys_data_client/resources/__init__.py` - Added Customers and Items exports
- `src/sonnys_data_client/_client.py` - Added functools.cached_property accessors for customers and items
- `src/sonnys_data_client/__init__.py` - Added Customers and Items to public API and __all__

## Decisions Made
- Module-level imports for resources in _client.py — verified no circular dependency exists since resources import from _resources.py (not _client.py)
- functools.cached_property for resource accessors — instantiated once per client lifetime

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Resource wiring pattern established for remaining resources (Employees, Sites, Giftcards, Washbooks, Recurring, Transactions)
- Ready for 06-02-PLAN.md: Employees and Sites resources

---
*Phase: 06-standard-resources*
*Completed: 2026-02-10*
