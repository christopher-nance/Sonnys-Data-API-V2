# Roadmap: Sonny's Data Client

## Current Milestone

No active milestone. v1.0 shipped 2026-02-10.

## Completed Milestones

### v1.0: Initial Release — SHIPPED 2026-02-10

Complete Python SDK wrapping the Sonny's Carwash Controls Data API with 8 resource types, auto-pagination, rate limiting, batch jobs, and pip-installable distribution.

**Stats:** 10 phases, 17 plans, 34 files, 3,783 LOC Python
**Archive:** [.planning/milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

<details>
<summary>Phases (all complete)</summary>

- [x] **Phase 1: Project Foundation** - Package scaffolding, SonnysClient class, dependency declarations
- [x] **Phase 2: HTTP Transport & Errors** - Request/response cycle, auth headers, exception hierarchy, error mapping
- [x] **Phase 3: Rate Limiting** - Per-instance sliding window, 429 backoff, retry logic
- [x] **Phase 4: Response Models** - Pydantic v2 models for all 8 resource types
- [x] **Phase 5: Resource Framework** - Base resource class, list/get patterns, auto-pagination
- [x] **Phase 6: Standard Resources** - Customers, Items, Employees, Sites
- [x] **Phase 7: Account Resources** - Giftcards, Washbooks, Recurring accounts
- [x] **Phase 8: Transaction Resources** - All transaction endpoints (list, by type, detail, v2)
- [x] **Phase 9: Batch Job System** - load-job, get-job-data, auto-polling
- [x] **Phase 10: Packaging & Distribution** - pip-install from GitHub, logging polish, integration tests

</details>
