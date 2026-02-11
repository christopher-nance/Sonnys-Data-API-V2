---
phase: 13-resource-guides
plan: 01
subsystem: docs
tags: [mkdocs, guides, customers, items, employees, sites, admonitions]

# Dependency graph
requires:
  - phase: 12-api-reference-setup
    provides: mkdocs-material site with API reference pages and nav structure
provides:
  - Guides nav section in mkdocs.yml with all 8 resource entries
  - Usage guides for Customers, Items, Employees, Sites with examples and model tables
affects: [13-02 account resource guides, 14-transaction-deep-dive, 15-account-resources]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guide structure: H1 title, overview, H2 Methods, H2 Examples, H2 Models, admonitions"

key-files:
  created:
    - docs/guides/customers.md
    - docs/guides/items.md
    - docs/guides/employees.md
    - docs/guides/sites.md
  modified:
    - mkdocs.yml

key-decisions:
  - "Consistent guide structure: overview, methods with signatures, realistic examples, model field tables, admonition tips"
  - "Nav lists all 8 resource guides upfront (4 created now, 4 placeholder entries for future phases)"

patterns-established:
  - "Guide template: H1 resource name → overview → H2 Methods with code signatures → H2 Examples with realistic Python → H2 Models with field tables → admonition blocks for notes/tips"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 13 Plan 01: Standard Resource Guides Summary

**4 resource usage guides (Customers, Items, Employees, Sites) with methods, realistic examples, model tables, and mkdocs Guides nav section**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T00:14:41Z
- **Completed:** 2026-02-11T00:18:08Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added Guides nav section to mkdocs.yml with all 8 resource entries (4 guides created, 4 placeholders for future phases)
- Created Customers guide with list/get methods, date filtering, nested Address access examples
- Created Items guide with list-only resource pattern, department grouping, site filtering examples
- Created Employees guide highlighting get_clock_entries custom method with date range and hours summarization examples
- Created Sites guide with non-paginated resource note and site code cross-reference tips

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Guides nav section + Customers & Items guides** - `dd593bc` (feat)
2. **Task 2: Employees & Sites guides** - `999f9f0` (feat)

## Files Created/Modified
- `mkdocs.yml` - Added Guides nav section between Home and API Reference
- `docs/guides/customers.md` - Customers guide with list/get, date filtering, Address access
- `docs/guides/items.md` - Items guide with list-only pattern, department grouping
- `docs/guides/employees.md` - Employees guide with get_clock_entries, hours summarization
- `docs/guides/sites.md` - Sites guide with non-paginated note, site code tips

## Decisions Made
- Established consistent guide structure: overview, methods with code signatures, realistic examples, model field tables, admonition blocks
- Listed all 8 resource guides in nav upfront — 4 created now, 4 as placeholders for Phases 14-15

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness
- Guide template pattern established for remaining 4 resources
- Ready for 13-02-PLAN.md (account resource guides)
- mkdocs build warns about 4 missing guide pages (expected until Phases 14-15 create them)

---
*Phase: 13-resource-guides*
*Completed: 2026-02-10*
