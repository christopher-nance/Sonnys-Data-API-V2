# Roadmap: Sonny's Data Client

## Milestones

- ✅ **v1.0 Initial Release** - [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) (Phases 1-10, shipped 2026-02-10)
- 🚧 **v1.1 Documentation** - Phases 11-18 (in progress)

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

## Phase Details

### 🚧 v1.1 Documentation (In Progress)

**Milestone Goal:** Comprehensive documentation suite — expanded README, auto-generated API reference, per-resource guides, and polished docstrings so any developer or AI agent can use the SDK without reading source code.

#### Phase 11: README Overhaul

**Goal**: Expand README with badges, table of contents, complete parameter documentation, and richer examples for every resource
**Depends on**: Previous milestone complete
**Research**: Unlikely (enhancing existing content)
**Plans**: 2

Plans:
- [ ] 11-01: README Structure & Client Docs (badges, ToC, constructor params)
- [ ] 11-02: Complete Resource Documentation (all 8 resources with param tables + examples)

#### Phase 12: API Reference Setup

**Goal**: Set up auto-generated API reference docs from docstrings using mkdocs or Sphinx, with Pydantic model rendering and GitHub Pages deployment
**Depends on**: Phase 11
**Research**: Likely (tooling decision — mkdocs vs Sphinx, theme selection, autodoc config)
**Research topics**: mkdocs-material vs Sphinx, autodoc plugins for Pydantic models, GitHub Pages deployment
**Plans**: TBD

Plans:
- [ ] 12-01: TBD (run /gsd:plan-phase 12 to break down)

#### Phase 13: Resource Guides

**Goal**: Per-resource usage guides with realistic examples for each of the 8 resources (customers, items, employees, sites, giftcards, washbooks, recurring, transactions)
**Depends on**: Phase 12
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: TBD

Plans:
- [ ] 13-01: TBD (run /gsd:plan-phase 13 to break down)

#### Phase 14: Transaction Deep Dive

**Goal**: Detailed guide for the most complex resource — list, list_by_type, list_v2, get, and load_job with parameter tables, response examples, and batch job workflow diagrams
**Depends on**: Phase 13
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: TBD

Plans:
- [ ] 14-01: TBD (run /gsd:plan-phase 14 to break down)

#### Phase 15: Account Resources Guide

**Goal**: Guide for giftcards, washbooks, and recurring accounts covering status tracking, modification history, and the relationship between account types
**Depends on**: Phase 14
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: TBD

Plans:
- [ ] 15-01: TBD (run /gsd:plan-phase 15 to break down)

#### Phase 16: Error Handling & Troubleshooting

**Goal**: Comprehensive error handling patterns guide — exception hierarchy usage, retry strategies, debugging with logging, and common issues with solutions
**Depends on**: Phase 15
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: TBD

Plans:
- [ ] 16-01: TBD (run /gsd:plan-phase 16 to break down)

#### Phase 17: Advanced Patterns

**Goal**: Advanced usage documentation — multi-site patterns, rate limiting behavior, logging configuration, integration recipes for analytics/automation pipelines
**Depends on**: Phase 16
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: TBD

Plans:
- [ ] 17-01: TBD (run /gsd:plan-phase 17 to break down)

#### Phase 18: Docstring Audit

**Goal**: Audit and complete all public API docstrings for consistency — ensure every class, method, and model has complete, accurate documentation matching the guides
**Depends on**: Phase 17
**Research**: Unlikely (internal code review)
**Plans**: TBD

Plans:
- [ ] 18-01: TBD (run /gsd:plan-phase 18 to break down)

## Progress

**Execution Order:**
Phases execute in numeric order: 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 11. README Overhaul | v1.1 | 0/2 | Planned | - |
| 12. API Reference Setup | v1.1 | 0/? | Not started | - |
| 13. Resource Guides | v1.1 | 0/? | Not started | - |
| 14. Transaction Deep Dive | v1.1 | 0/? | Not started | - |
| 15. Account Resources | v1.1 | 0/? | Not started | - |
| 16. Error & Troubleshoot | v1.1 | 0/? | Not started | - |
| 17. Advanced Patterns | v1.1 | 0/? | Not started | - |
| 18. Docstring Audit | v1.1 | 0/? | Not started | - |
