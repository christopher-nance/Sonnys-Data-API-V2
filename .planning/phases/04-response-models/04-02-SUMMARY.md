---
phase: 04-response-models
plan: 02
subsystem: api
tags: [pydantic, models, items, giftcards, washbooks, recurring, alias-override]

# Dependency graph
requires:
  - phase: 04-response-models plan 01
    provides: SonnysModel base class, established model patterns
provides:
  - Item model for merchandise/service items
  - GiftcardListItem model for giftcard accounts
  - 6 Washbook models (Tag, Vehicle, Customer, RecurringInfo, ListItem, Detail)
  - 7 Recurring models (Status, Billing, ListItem, Detail, StatusChange, ModificationEntry, Modification)
  - Shared sub-objects (WashbookTag, WashbookVehicle, WashbookCustomer) reused by Recurring
affects: [04-03, 06-standard-resources, 07-account-resources]

# Tech tracking
tech-stack:
  added: [pydantic.Field for explicit alias override]
  patterns: [alias_generator=None override for snake_case API responses, Field(alias=...) for non-standard casing]

key-files:
  created:
    - src/sonnys_data_client/types/_items.py
    - src/sonnys_data_client/types/_giftcards.py
    - src/sonnys_data_client/types/_washbooks.py
    - src/sonnys_data_client/types/_recurring.py
  modified: []

key-decisions:
  - "RecurringBilling.last_four_cc uses explicit Field(alias='lastFourCC') for non-standard casing"
  - "RecurringStatusChange overrides alias_generator=None because API returns snake_case"
  - "Shared sub-objects (WashbookTag, WashbookVehicle, WashbookCustomer) live in _washbooks.py and are imported by _recurring.py"

patterns-established:
  - "Explicit alias override: Field(alias='...') when to_camel produces wrong casing"
  - "alias_generator=None override: for API endpoints returning snake_case instead of camelCase"
  - "Cross-module import: _recurring.py imports shared sub-objects from _washbooks.py"

issues-created: []

# Metrics
duration: 3 min
completed: 2026-02-10
---

# Phase 4 Plan 2: Item, Giftcard, Washbook & Recurring Models Summary

**15 Pydantic v2 models across 4 files — items, giftcards, washbook account ecosystem with shared sub-objects, and recurring membership models with alias overrides for non-standard API casing**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-10T16:14:00Z
- **Completed:** 2026-02-10T16:17:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Item and GiftcardListItem models for merchandise and prepaid card resources
- 6 washbook models covering the full account ecosystem: tags, vehicles, customers, recurring info, list items, and detail
- 7 recurring models with explicit alias overrides — Field(alias="lastFourCC") for non-standard casing and alias_generator=None for snake_case API responses
- Shared sub-objects (WashbookTag, WashbookVehicle, WashbookCustomer) imported by both _washbooks.py and _recurring.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Item and GiftcardListItem models** - `dfbba86` (feat)
2. **Task 2: Create Washbook models with shared sub-objects** - `d23da82` (feat)
3. **Task 3: Create Recurring models with alias overrides** - `c49ec65` (feat)

## Files Created/Modified
- `src/sonnys_data_client/types/_items.py` - Item model (7 fields)
- `src/sonnys_data_client/types/_giftcards.py` - GiftcardListItem model (6 fields)
- `src/sonnys_data_client/types/_washbooks.py` - WashbookTag, WashbookVehicle, WashbookCustomer, WashbookRecurringInfo, WashbookListItem, Washbook
- `src/sonnys_data_client/types/_recurring.py` - RecurringStatus, RecurringBilling, RecurringListItem, Recurring, RecurringStatusChange, RecurringModificationEntry, RecurringModification

## Decisions Made
- RecurringBilling.last_four_cc uses explicit `Field(alias="lastFourCC")` because `to_camel("last_four_cc")` produces `"lastFourCc"` not `"lastFourCC"`
- RecurringStatusChange overrides with `alias_generator=None` because this API endpoint returns snake_case fields
- Shared sub-objects live in _washbooks.py and are imported by _recurring.py (no circular dependency)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed RecurringStatusChange alias_generator inheritance**
- **Found during:** Task 3 (Recurring models)
- **Issue:** Plan specified `model_config = ConfigDict(populate_by_name=True)` but Pydantic v2 merges child ConfigDict with parent, so `alias_generator=to_camel` was still inherited from SonnysModel
- **Fix:** Explicitly set `alias_generator=None` in the override ConfigDict
- **Verification:** `RecurringStatusChange.model_dump(by_alias=True)` returns snake_case keys
- **Committed in:** `c49ec65` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix necessary for correct snake_case serialization. No scope creep.

## Issues Encountered
None

## Next Phase Readiness
- All prepaid account ecosystem models complete (items, giftcards, washbooks, recurring)
- Ready for 04-03-PLAN.md (employee and site models — final plan in Phase 4)

---
*Phase: 04-response-models*
*Completed: 2026-02-10*
