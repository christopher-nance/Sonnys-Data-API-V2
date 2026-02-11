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

#### Phase 11: README Overhaul -- COMPLETE

**Goal**: Expand README with badges, table of contents, complete parameter documentation, and richer examples for every resource
**Depends on**: Previous milestone complete
**Research**: Unlikely (enhancing existing content)
**Plans**: 2
**Completed**: 2026-02-10

Plans:
- [x] 11-01: README Structure & Client Docs (badges, ToC, constructor params)
- [x] 11-02: Complete Resource Documentation (all 8 resources with param tables + examples)

#### Phase 12: API Reference Setup -- COMPLETE

**Goal**: Set up auto-generated API reference docs from docstrings using mkdocs or Sphinx, with Pydantic model rendering and GitHub Pages deployment
**Depends on**: Phase 11
**Research**: Likely (tooling decision — mkdocs vs Sphinx, theme selection, autodoc config)
**Research topics**: mkdocs-material vs Sphinx, autodoc plugins for Pydantic models, GitHub Pages deployment
**Plans**: 2
**Completed**: 2026-02-10

Plans:
- [x] 12-01: MkDocs Material Setup (docs dependencies, mkdocs.yml, landing page)
- [x] 12-02: API Reference Pages & GitHub Pages Deploy

#### Phase 13: Resource Guides -- COMPLETE

**Goal**: Per-resource usage guides with realistic examples for each of the 8 resources (customers, items, employees, sites, giftcards, washbooks, recurring, transactions)
**Depends on**: Phase 12
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: 2
**Completed**: 2026-02-10

Plans:
- [x] 13-01: Standard Resource Guides (Customers, Items, Employees, Sites + Guides nav)
- [x] 13-02: Account & Transaction Resource Guides (Giftcards, Washbooks, Recurring, Transactions)

#### Phase 14: Transaction Deep Dive -- COMPLETE

**Goal**: Detailed guide for the most complex resource — list, list_by_type, list_v2, get, and load_job with parameter tables, response examples, and batch job workflow diagrams
**Depends on**: Phase 13
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: 2
**Completed**: 2026-02-11

Plans:
- [x] 14-01: Method Comparison & Batch Job Workflow (comparison table, parameter tables, batch job deep dive)
- [x] 14-02: Advanced Patterns & Deploy (multi-day exports, error handling, cross-resource lookups, gh-pages deploy)

#### Phase 15: Account Resources Guide -- COMPLETE

**Goal**: Guide for giftcards, washbooks, and recurring accounts covering status tracking, modification history, and the relationship between account types
**Depends on**: Phase 14
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: 1
**Completed**: 2026-02-11

Plans:
- [x] 15-01: Advanced Account Patterns & Deploy (recurring method comparison, churn analysis, billing report, giftcard liability tracking)

#### Phase 16: Error Handling & Troubleshooting -- COMPLETE

**Goal**: Comprehensive error handling patterns guide — exception hierarchy usage, retry strategies, debugging with logging, and common issues with solutions
**Depends on**: Phase 15
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: 2
**Completed**: 2026-02-11

Plans:
- [x] 16-01: Error Handling Patterns Guide (hierarchy, catching, attributes, per-type guidance, retry recipes)
- [x] 16-02: Logging, Troubleshooting & Deploy (logging config, common issues, mkdocs nav, gh-pages deploy)

#### Phase 17: Advanced Patterns -- COMPLETE

**Goal**: Advanced usage documentation — multi-site patterns, rate limiting behavior, logging configuration, integration recipes for analytics/automation pipelines
**Depends on**: Phase 16
**Research**: Unlikely (internal documentation based on existing code)
**Plans**: 2
**Completed**: 2026-02-11

Plans:
- [x] 17-01: Multi-Site & Performance Patterns (multi-site operations, rate limiting deep dive, performance optimization)
- [x] 17-02: Integration Recipes & Deploy (integration recipes, mkdocs nav update, gh-pages deploy)

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
| 11. README Overhaul | v1.1 | 2/2 | Complete | 2026-02-10 |
| 12. API Reference Setup | v1.1 | 2/2 | Complete | 2026-02-10 |
| 13. Resource Guides | v1.1 | 2/2 | Complete | 2026-02-10 |
| 14. Transaction Deep Dive | v1.1 | 2/2 | Complete | 2026-02-11 |
| 15. Account Resources | v1.1 | 1/1 | Complete | 2026-02-11 |
| 16. Error & Troubleshoot | v1.1 | 2/2 | Complete | 2026-02-11 |
| 17. Advanced Patterns | v1.1 | 2/2 | Complete | 2026-02-11 |
| 18. Docstring Audit | v1.1 | 0/? | Not started | - |
