---
phase: 18-docstring-audit
plan: 01
subsystem: docs
tags: [docstrings, exceptions, resources, mkdocstrings, api-reference]

requires:
  - phase: 12-api-reference-setup
    plan: 02
    provides: mkdocstrings autodoc rendering for all public classes
provides:
  - Complete docstrings on all 10 exception classes
  - SonnysModel base class docstring
  - Module docstrings for all type files
  - Enriched resource class docstrings with API documentation
affects: [18-02, 18-03]

tech-stack:
  added: []
  patterns: [google-docstring-style-for-all-classes]

key-files:
  created: []
  modified:
    - src/sonnys_data_client/_exceptions.py
    - src/sonnys_data_client/types/_base.py
    - src/sonnys_data_client/types/__init__.py
    - src/sonnys_data_client/types/_customers.py
    - src/sonnys_data_client/types/_employees.py
    - src/sonnys_data_client/types/_giftcards.py
    - src/sonnys_data_client/types/_items.py
    - src/sonnys_data_client/types/_sites.py
    - src/sonnys_data_client/types/_washbooks.py
    - src/sonnys_data_client/types/_recurring.py
    - src/sonnys_data_client/types/_transactions.py
    - src/sonnys_data_client/resources/_customers.py
    - src/sonnys_data_client/resources/_employees.py
    - src/sonnys_data_client/resources/_giftcards.py
    - src/sonnys_data_client/resources/_items.py
    - src/sonnys_data_client/resources/_sites.py
    - src/sonnys_data_client/resources/_washbooks.py
    - src/sonnys_data_client/resources/_recurring.py
    - src/sonnys_data_client/resources/_transactions.py

key-decisions:
  - "Google docstring style with Attributes sections for exception classes"

patterns-established:
  - "Exception docstrings include HTTP status codes and usage context"
  - "Resource docstrings document inherited methods, custom methods, and supported filters"

issues-created: []

duration: 4min
completed: 2026-02-11
---

# 18-01 Summary: Add docstrings to exceptions, SonnysModel, and resource classes

Added Google-style docstrings to all 10 exception classes, the SonnysModel base class, all type module files, and enriched all 8 resource class docstrings with comprehensive API documentation for mkdocstrings rendering.

## Performance

No runtime impact -- all changes are docstrings only.

## Accomplishments

- Added class docstrings to all 10 exception classes with HTTP status codes and usage context
- Added Attributes sections to `APIError` and `APIStatusError` for mkdocstrings rendering
- Added class docstring to `SonnysModel` documenting camelCase alias behavior
- Added module-level docstrings to all 9 type module files (`_base.py`, `__init__.py`, and 7 domain modules)
- Enriched all 8 resource class docstrings with multi-line descriptions covering:
  - What each resource provides (endpoints covered)
  - Inherited methods (`list()`, `get()`) with return types and supported filters
  - Custom methods unique to each resource (e.g., `get_clock_entries()`, `load_job()`)
- No existing method docstrings were modified

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `f2b13b1` | Add docstrings to exceptions, SonnysModel, and type modules |
| Task 2 | `8b34708` | Enrich resource class docstrings with API documentation |

## Files Created

None.

## Files Modified

**Task 1 (11 files):**
- `src/sonnys_data_client/_exceptions.py` -- Added class docstrings to all 10 exception classes
- `src/sonnys_data_client/types/_base.py` -- Added module docstring and SonnysModel class docstring
- `src/sonnys_data_client/types/__init__.py` -- Added module docstring
- `src/sonnys_data_client/types/_customers.py` -- Added module docstring
- `src/sonnys_data_client/types/_employees.py` -- Added module docstring
- `src/sonnys_data_client/types/_giftcards.py` -- Added module docstring
- `src/sonnys_data_client/types/_items.py` -- Added module docstring
- `src/sonnys_data_client/types/_sites.py` -- Added module docstring
- `src/sonnys_data_client/types/_washbooks.py` -- Added module docstring
- `src/sonnys_data_client/types/_recurring.py` -- Added module docstring
- `src/sonnys_data_client/types/_transactions.py` -- Added module docstring

**Task 2 (8 files):**
- `src/sonnys_data_client/resources/_customers.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_employees.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_giftcards.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_items.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_sites.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_washbooks.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_recurring.py` -- Enriched class docstring
- `src/sonnys_data_client/resources/_transactions.py` -- Enriched class docstring

## Decisions Made

- Used Google docstring style with `Attributes:` sections for exception classes that expose public attributes (`APIError.message`, `APIStatusError.status_code/body/error_type`)
- Resource class docstrings use Sphinx cross-references (`:class:` roles) for mkdocstrings rendering
- Kept resource docstrings concise (5-12 lines) to render cleanly in the API reference
- Documented the intentional API typo in `giftcard-liablilty` path in the Giftcards docstring

## Deviations from Plan

None. All tasks executed as specified.

## Issues Encountered

None.

## Next Phase Readiness

Plan 18-02 (Pydantic model docstrings) and 18-03 (method docstring audit) can proceed. All module-level docstrings are in place for type files, providing the foundation for adding individual model class docstrings in 18-02.
