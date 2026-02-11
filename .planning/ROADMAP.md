# Roadmap: Sonny's Data Client

## Milestones

- ✅ **v1.0 Initial Release** — [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) (Phases 1-10, shipped 2026-02-10)
- ✅ **v1.1 Documentation** — [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md) (Phases 11-18, shipped 2026-02-11)
- 🚧 **v1.2 Improvements** — Phases 19-26 (in progress)

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

### v1.1: Documentation — SHIPPED 2026-02-11

Comprehensive documentation suite — expanded README, auto-generated API reference on GitHub Pages, per-resource usage guides, and complete docstring coverage.

**Stats:** 8 phases, 16 plans, 72 files, 4,068 LOC docs + docstrings
**Archive:** [.planning/milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

<details>
<summary>Phases (all complete)</summary>

- [x] **Phase 11: README Overhaul** (2/2 plans) — completed 2026-02-10
- [x] **Phase 12: API Reference Setup** (2/2 plans) — completed 2026-02-10
- [x] **Phase 13: Resource Guides** (2/2 plans) — completed 2026-02-10
- [x] **Phase 14: Transaction Deep Dive** (2/2 plans) — completed 2026-02-11
- [x] **Phase 15: Account Resources Guide** (1/1 plan) — completed 2026-02-11
- [x] **Phase 16: Error Handling & Troubleshooting** (2/2 plans) — completed 2026-02-11
- [x] **Phase 17: Advanced Patterns** (2/2 plans) — completed 2026-02-11
- [x] **Phase 18: Docstring Audit** (3/3 plans) — completed 2026-02-11

</details>

### 🚧 v1.2 Improvements (In Progress)

**Milestone Goal:** Add client-side business analytics via `client.stats.*` — conversion rate, total sales, total washes, retail wash count, and new memberships sold.

#### Phase 19: Stats Module Foundation

**Goal**: Create StatsResource class, wire `client.stats` property, date range parameter utilities
**Depends on**: Previous milestone complete
**Research**: Unlikely (internal patterns, mirrors existing resource architecture)
**Plans**: 2/2 complete

Plans:
- [x] 19-01: Date Range Parsing & Validation (TDD) — completed 2026-02-11
- [x] 19-02: StatsResource Class & Client Wiring — completed 2026-02-11

#### Phase 20: Data Fetching Layer

**Goal**: Efficient bulk data retrieval for stats computation — fetch transactions and recurring data for a date range without redundant API calls
**Depends on**: Phase 19
**Research**: Unlikely (existing SDK pagination and fetching patterns)
**Plans**: TBD

Plans:
- [ ] 20-01: TBD

#### Phase 21: Revenue & Sales Stats

**Goal**: `client.stats.total_sales(start, end)` with breakdowns by transaction type
**Depends on**: Phase 20
**Research**: Unlikely (aggregation over existing transaction data)
**Plans**: TBD

Plans:
- [ ] 21-01: TBD

#### Phase 22: Wash Analytics

**Goal**: `client.stats.total_washes()` and `client.stats.retail_wash_count()` from transaction type filtering
**Depends on**: Phase 20
**Research**: Unlikely (transaction type filtering)
**Plans**: TBD

Plans:
- [ ] 22-01: TBD

#### Phase 23: Membership Analytics

**Goal**: `client.stats.new_memberships_sold()` from recurring account status change data
**Depends on**: Phase 20
**Research**: Unlikely (recurring status change analysis)
**Plans**: TBD

Plans:
- [ ] 23-01: TBD

#### Phase 24: Conversion Rate

**Goal**: `client.stats.conversion_rate()` = new_memberships / (new_memberships + retail_washes)
**Depends on**: Phase 22, Phase 23
**Research**: Unlikely (composite of prior phase outputs)
**Plans**: TBD

Plans:
- [ ] 24-01: TBD

#### Phase 25: Stats Report

**Goal**: `client.stats.report(start, end)` returning all KPIs in one call with single data fetch for efficiency
**Depends on**: Phase 24
**Research**: Unlikely (combines prior phases into unified interface)
**Plans**: TBD

Plans:
- [ ] 25-01: TBD

#### Phase 26: Stats Documentation & Testing

**Goal**: Usage guide, docstrings, unit tests, UAT validation with real data
**Depends on**: Phase 25
**Research**: Unlikely (established doc and test patterns from v1.1)
**Plans**: TBD

Plans:
- [ ] 26-01: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Project Foundation | v1.0 | 1/1 | Complete | 2026-02-10 |
| 2. HTTP Transport & Errors | v1.0 | 2/2 | Complete | 2026-02-10 |
| 3. Rate Limiting | v1.0 | 2/2 | Complete | 2026-02-10 |
| 4. Response Models | v1.0 | 3/3 | Complete | 2026-02-10 |
| 5. Resource Framework | v1.0 | 1/1 | Complete | 2026-02-10 |
| 6. Standard Resources | v1.0 | 2/2 | Complete | 2026-02-10 |
| 7. Account Resources | v1.0 | 2/2 | Complete | 2026-02-10 |
| 8. Transaction Resources | v1.0 | 2/2 | Complete | 2026-02-10 |
| 9. Batch Job System | v1.0 | 1/1 | Complete | 2026-02-10 |
| 10. Packaging & Distribution | v1.0 | 1/1 | Complete | 2026-02-10 |
| 11. README Overhaul | v1.1 | 2/2 | Complete | 2026-02-10 |
| 12. API Reference Setup | v1.1 | 2/2 | Complete | 2026-02-10 |
| 13. Resource Guides | v1.1 | 2/2 | Complete | 2026-02-10 |
| 14. Transaction Deep Dive | v1.1 | 2/2 | Complete | 2026-02-11 |
| 15. Account Resources Guide | v1.1 | 1/1 | Complete | 2026-02-11 |
| 16. Error & Troubleshoot | v1.1 | 2/2 | Complete | 2026-02-11 |
| 17. Advanced Patterns | v1.1 | 2/2 | Complete | 2026-02-11 |
| 18. Docstring Audit | v1.1 | 3/3 | Complete | 2026-02-11 |
| 19. Stats Module Foundation | v1.2 | 2/2 | Complete | 2026-02-11 |
| 20. Data Fetching Layer | v1.2 | 0/? | Not started | - |
| 21. Revenue & Sales Stats | v1.2 | 0/? | Not started | - |
| 22. Wash Analytics | v1.2 | 0/? | Not started | - |
| 23. Membership Analytics | v1.2 | 0/? | Not started | - |
| 24. Conversion Rate | v1.2 | 0/? | Not started | - |
| 25. Stats Report | v1.2 | 0/? | Not started | - |
| 26. Stats Documentation & Testing | v1.2 | 0/? | Not started | - |
