# Sonny's Data Client

## What This Is

A Python module (`sonnys-data-client`) that provides a clean, reliable bridge between multiple applications and the Sonny's Carwash Controls Data API. It wraps the REST API with a resource-based interface, Pydantic models, built-in rate limiting, and auto-pagination so consuming applications (analytics, internal tools, automations) can pull car wash data without worrying about HTTP plumbing.

## Core Value

Dead-simple interface with rock-solid reliability — any developer or AI agent picks it up instantly, and it never crashes your apps.

## Requirements

### Validated

- [x] Class-based client with per-instance credentials (`SonnysClient(api_id=..., api_key=..., site_code=...)`) — v1.0
- [x] Resource-based call pattern (`client.transactions.list()`, `client.customers.get(id)`) — v1.0
- [x] Pydantic models for all API response types (transactions, customers, items, prepaid accounts, employees, sites) — v1.0
- [x] Built-in rate limiting (20 requests per 15-second window, automatic backoff on 429s) — v1.0
- [x] Auto-pagination — list methods fetch all pages transparently, return complete results — v1.0
- [x] Auto-polling for batch job endpoints (load-job → poll get-job-data → return final results) — v1.0
- [x] Custom exception hierarchy mapped to API error types (AuthError, RateLimitError, ValidationError, NotFoundError, ServerError) — v1.0
- [x] Python standard logging (debug level shows requests/responses, configurable by caller) — v1.0
- [x] pip-installable from GitHub (`pip install git+https://github.com/...`) — v1.0
- [x] Full endpoint coverage for all API resources — v1.0:
  - Transactions (list, list by type, get detail, v2 list, batch job)
  - Customers (list, get detail)
  - Items (list)
  - Giftcards (list, get detail)
  - Washbooks (list, get detail)
  - Recurring accounts (list, get detail, status history)
  - Employees (list, get detail with clock entries)
  - Sites (list)

### Active

(None — v1.0 scope fully delivered)

### Out of Scope

- Caching layer — always hits the API fresh; consuming apps can implement their own caching
- Sandbox environment support — production only (`trigonapi.sonnyscontrols.com/v1`)
- Async support — synchronous only; async can be added in a future version if needed
- Business logic / data transformation — module returns API data as Pydantic models, no domain logic

## Context

- **API Spec:** Sonny's Carwash Controls Data API v0.2.0 (OpenAPI)
- **Base URL:** `https://trigonapi.sonnyscontrols.com/v1`
- **Auth:** Header-based — `X-Sonnys-API-ID`, `X-Sonnys-API-Key`, optional `X-Sonnys-Site-Code`
- **Rate Limit:** 20 requests per 15-second window per API ID
- **Pagination:** `limit` (1-100) and `offset` (1+) query params, responses include `total` count
- **Multi-credential use case:** User operates two databases (WashU and Icon) with separate API credentials — a single application may instantiate multiple clients
- **Consumers:** Mix of data analytics/BI, internal operational tools, and scheduled automation scripts
- **API pinned at current spec** — module built against v0.2.0, updated manually when API changes

### API Endpoints Reference

| Resource | Endpoints |
|----------|-----------|
| Transactions | `GET /transaction`, `GET /transaction/type/{item_type}`, `GET /transaction/{trans_id}`, `GET /transaction/version-2`, `POST /transaction/load-job`, `GET /transaction/get-job-data` |
| Customers | `GET /customer`, `GET /customer/{customer_id}` |
| Items | `GET /item` |
| Giftcards | `GET /giftcard`, `GET /giftcard/{account_id}` |
| Washbooks | `GET /washbook`, `GET /washbook/{account_id}` |
| Recurring | `GET /recurring`, `GET /recurring/{account_id}`, `GET /recurring-status` |
| Employees | `GET /employee`, `GET /employee/{employee_id}` |
| Sites | `GET /site` |

### API Error Types

| Error Type | HTTP Status | Maps To |
|------------|-------------|---------|
| MissingClientCredentialsError | 403 | AuthError |
| BadClientCredentialsError | 403 | AuthError |
| MismatchCredentialsError | 403 | AuthError |
| NotAuthorizedError | 403 | AuthError |
| BadSiteCredentialsError | 403 | AuthError |
| NotAuthorizedSiteCredentialsError | 403 | AuthError |
| NotAuthorizedSiteArgsError | 403 | AuthError |
| RequestRateExceedError | 429 | RateLimitError |
| PayloadValidationError | 422 | ValidationError |
| InvalidPayloadRequestTimestampError | 400 | ValidationError |
| EntityNotFoundError | 404 | NotFoundError |
| UnexpectedFailure | 400 | APIError |
| ServerUnexpectedFailure | 500 | ServerError |

## Constraints

- **Distribution:** pip-installable from GitHub — `pip install git+https://github.com/.../sonnys-data-client.git`
- **Dependencies:** Minimal — `requests` (HTTP) + `pydantic` (models) as core dependencies
- **Python version:** 3.10+ (modern Python, leverage type hints and Pydantic v2)
- **API rate limit:** 20 req/15s per API ID — module must enforce this internally per client instance

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Resource-based API (`client.transactions.list()`) | Intuitive, discoverable, mirrors API structure | Validated v1.0 — 8 resource classes, clean `client.resource.method()` pattern |
| Pydantic v2 models for responses | Typed, validated, autocomplete support in IDEs | Validated v1.0 — 30 models with camelCase aliases, live API tested |
| Per-instance rate limiting | Multiple clients with different API IDs have independent rate limits | Validated v1.0 — sliding window 20 req/15s with exponential backoff |
| Auto-pagination by default | Callers shouldn't manage offset/limit loops for common operations | Validated v1.0 — transparent offset/limit loop with null-safe total handling |
| Auto-poll batch jobs | load-job → poll → return simplifies the most complex API pattern | Validated v1.0 — status-driven polling with configurable timeout/interval |
| Production only (no sandbox toggle) | Simplifies client, sandbox not needed for current use case | Validated v1.0 — single base URL, no environment switching |
| `requests` over `httpx` | Simpler, synchronous-only scope, widely understood | Validated v1.0 — requests + persistent session with auth headers |

---
*Last updated: 2026-02-10 — v1.0 shipped (3,783 LOC Python, 30 Pydantic models, 8 resource classes, 110 unit tests)*
