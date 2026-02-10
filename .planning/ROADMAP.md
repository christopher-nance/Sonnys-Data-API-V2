# Roadmap: Sonny's Data Client

## Overview

Build a pip-installable Python module that wraps the Sonny's Carwash Controls Data API with a resource-based interface, Pydantic models, built-in rate limiting, and auto-pagination. Starting from package scaffolding, we layer in HTTP transport, error handling, rate limiting, and response models before implementing resource classes for each API endpoint group — culminating in a polished, pip-installable package.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Project Foundation** - Package scaffolding, SonnysClient class, dependency declarations
- [x] **Phase 2: HTTP Transport & Errors** - Request/response cycle, auth headers, exception hierarchy, error mapping
- [ ] **Phase 3: Rate Limiting** - Per-instance sliding window, 429 backoff, retry logic
- [ ] **Phase 4: Response Models** - Pydantic v2 models for all 8 resource types
- [ ] **Phase 5: Resource Framework** - Base resource class, list/get patterns, auto-pagination
- [ ] **Phase 6: Standard Resources** - Customers, Items, Employees, Sites
- [ ] **Phase 7: Account Resources** - Giftcards, Washbooks, Recurring accounts
- [ ] **Phase 8: Transaction Resources** - All transaction endpoints (list, by type, detail, v2)
- [ ] **Phase 9: Batch Job System** - load-job, get-job-data, auto-polling
- [ ] **Phase 10: Packaging & Distribution** - pip-install from GitHub, logging polish, integration tests

## Phase Details

### Phase 1: Project Foundation
**Goal**: Establish the Python package structure with pyproject.toml, src layout, SonnysClient class shell, and core dependencies (requests + pydantic)
**Depends on**: Nothing (first phase)
**Research**: Unlikely (standard Python packaging patterns)
**Plans**: TBD

Plans:
- [x] 01-01: Package scaffolding and SonnysClient class

### Phase 2: HTTP Transport & Errors
**Goal**: Implement the HTTP session layer with auth header injection, request/response methods, custom exception hierarchy, and mapping of all API error types to client exceptions
**Depends on**: Phase 1
**Research**: Likely (need exact API error response shapes)
**Research topics**: API error response format, exact HTTP status codes and error type strings, error response body structure
**Plans**: TBD

Plans:
- [x] 02-01: Exception hierarchy
- [x] 02-02: Error body parsing and status mapping (TDD)

### Phase 3: Rate Limiting
**Goal**: Implement per-instance sliding window rate limiter (20 req/15s), automatic backoff on 429 responses, and retry logic
**Depends on**: Phase 2
**Research**: Unlikely (well-known sliding window algorithm, internal implementation)
**Plans**: 2

Plans:
- [ ] 03-01: Sliding window rate limiter (TDD)
- [ ] 03-02: HTTP request method with 429 retry (TDD)

### Phase 4: Response Models
**Goal**: Define Pydantic v2 models for all API response types — transactions, customers, items, giftcards, washbooks, recurring accounts, employees, and sites
**Depends on**: Phase 1
**Research**: Likely (need exact API response field names, types, and structures)
**Research topics**: Full API response shapes per endpoint — field names, types, nesting, optional vs required fields
**Plans**: TBD

Plans:
- [ ] 04-01: Transaction and customer models
- [ ] 04-02: Item, giftcard, washbook, and recurring models
- [ ] 04-03: Employee and site models

### Phase 5: Resource Framework
**Goal**: Build the base resource class with reusable list/get method patterns and auto-pagination logic (offset/limit loop using total count)
**Depends on**: Phase 2, Phase 4
**Research**: Unlikely (internal design pattern, pagination params documented)
**Plans**: TBD

Plans:
- [ ] 05-01: Base resource class and auto-pagination

### Phase 6: Standard Resources
**Goal**: Implement resource classes for Customers (list, get), Items (list), Employees (list, get with clock entries), and Sites (list)
**Depends on**: Phase 5
**Research**: Unlikely (builds on framework + models from prior phases)
**Plans**: TBD

Plans:
- [ ] 06-01: Customers and Items resources
- [ ] 06-02: Employees and Sites resources

### Phase 7: Account Resources
**Goal**: Implement resource classes for Giftcards (list, get), Washbooks (list, get), and Recurring accounts (list, get, status history)
**Depends on**: Phase 5
**Research**: Unlikely (same list/get patterns, recurring-status is straightforward)
**Plans**: TBD

Plans:
- [ ] 07-01: Giftcards and Washbooks resources
- [ ] 07-02: Recurring resource with status history

### Phase 8: Transaction Resources
**Goal**: Implement the transaction resource with all endpoints — list, list by type, get detail, and v2 list
**Depends on**: Phase 5
**Research**: Likely (v2 endpoint differences from v1, query parameter variations)
**Research topics**: Transaction v2 vs v1 response differences, filtering/query params per transaction endpoint
**Plans**: TBD

Plans:
- [ ] 08-01: Transaction list, by-type, and detail
- [ ] 08-02: Transaction v2 list endpoint

### Phase 9: Batch Job System
**Goal**: Implement the transaction batch job flow — POST load-job, poll get-job-data, auto-poll loop with configurable timeout and interval
**Depends on**: Phase 8
**Research**: Likely (load-job request format, polling semantics, completion indicators)
**Research topics**: POST load-job payload structure, get-job-data response lifecycle, job status values, polling interval recommendations
**Plans**: TBD

Plans:
- [ ] 09-01: Batch job submission and polling

### Phase 10: Packaging & Distribution
**Goal**: Finalize pip-installable package from GitHub, polish logging configuration, run integration smoke tests, ensure clean install experience
**Depends on**: Phase 9
**Research**: Unlikely (standard pyproject.toml + GitHub pip install)
**Plans**: TBD

Plans:
- [ ] 10-01: Package finalization and install testing

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Foundation | 1/1 | Complete | 2026-02-10 |
| 2. HTTP Transport & Errors | 2/2 | Complete | 2026-02-10 |
| 3. Rate Limiting | 0/2 | Not started | - |
| 4. Response Models | 0/3 | Not started | - |
| 5. Resource Framework | 0/1 | Not started | - |
| 6. Standard Resources | 0/2 | Not started | - |
| 7. Account Resources | 0/2 | Not started | - |
| 8. Transaction Resources | 0/2 | Not started | - |
| 9. Batch Job System | 0/1 | Not started | - |
| 10. Packaging & Distribution | 0/1 | Not started | - |
