# Phase 8: Transaction Resources - Research

**Researched:** 2026-02-10
**Domain:** REST API wrapping — transaction endpoints with multiple list variants and path-param filtering
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Sonny's Data API transaction endpoints to understand the four endpoints Phase 8 must implement: v1 list, list-by-type (path param), detail, and v2 list. All Pydantic models already exist from Phase 4; the resource framework from Phase 5 provides `ListableResource`/`GettableResource` mixins and the `_paginated_fetch` helper from Phase 7 handles custom paginated endpoints.

Key finding: The `list_by_type` endpoint uses a **path parameter** (`/transaction/type/{item_type}`) rather than a query parameter — this is unique among all resources. The v2 endpoint (`/transaction/version-2`) uses a different path and returns `TransactionV2ListItem` (extends v1 with `customerId`, `isRecurringPlanSale`, `isRecurringPlanRedemption`, `transactionStatus`). All list endpoints share the same query parameters: `startDate`, `endDate`, `site`, `region` (plus standard `limit`/`offset`).

**Primary recommendation:** Build `Transactions` class inheriting `ListableResource` + `GettableResource`. Default `list()` uses v1 path. Add `list_by_type(item_type)` and `list_v2()` as custom methods using `_paginated_fetch`. All three list methods share the same `startDate`/`endDate`/`site`/`region` query params passed as `**params`.
</research_summary>

<standard_stack>
## Standard Stack

No new libraries needed — Phase 8 uses only existing project infrastructure:

### Core (Already Built)
| Component | Phase | Purpose | Status |
|-----------|-------|---------|--------|
| `ListableResource` | 5 | Paginated list with auto-pagination | Ready |
| `GettableResource` | 5 | Detail-by-ID endpoint | Ready |
| `_paginated_fetch` | 7 | Custom paginated endpoint helper | Ready (in RecurringAccounts) |
| Transaction models | 4 | `TransactionListItem`, `TransactionV2ListItem`, `Transaction` | Ready |

### Note on `_paginated_fetch` Reuse
The `_paginated_fetch` helper currently lives in `RecurringAccounts`. Phase 8's `Transactions` class needs the same helper for `list_by_type()` and `list_v2()`. Two options:
1. **Duplicate** — Copy the helper into `Transactions` (matches RecurringAccounts pattern)
2. **Extract to BaseResource** — Move to `BaseResource` for shared use

Recommend option 1 (duplicate) for consistency with existing pattern. The helper is 20 lines — not worth refactoring the base class.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Resource Class Structure
```python
class Transactions(ListableResource, GettableResource):
    # Standard list() via ListableResource
    _path = "/transaction"
    _items_key = "transactions"
    _model = TransactionListItem
    _default_limit = 100
    _paginated = True

    # Standard get() via GettableResource
    _detail_path = "/transaction/{id}"
    _detail_model = Transaction

    # Custom methods for type-filtered and v2 endpoints
    def list_by_type(self, item_type: str, **params) -> list[TransactionListItem]: ...
    def list_v2(self, **params) -> list[TransactionV2ListItem]: ...
```

### Pattern: Path-Parameter Filtering (list_by_type)
**What:** The `/transaction/type/{item_type}` endpoint uses a path parameter, not a query parameter.
**How to implement:** Build path string dynamically: `f"/transaction/type/{item_type}"`
**Valid `item_type` values:** `wash`, `prepaid-wash`, `recurring`, `washbook`, `giftcard`, `merchandise`, `house-account`
**Response:** Same structure as v1 list — `data.transactions[]` with `total`/`offset`/`limit`

### Pattern: Alternate List Endpoint (list_v2)
**What:** The `/transaction/version-2` endpoint returns enriched list items (`TransactionV2ListItem`).
**How to implement:** Custom method using `_paginated_fetch` with different path and model.
**Response:** Same pagination structure — `data.transactions[]` with `total`/`offset`/`limit`

### Anti-Patterns to Avoid
- **Don't make v2 a parameter on list():** v1 and v2 are separate endpoints with different response models — they should be separate methods.
- **Don't validate item_type in Python:** The API returns a clear error for invalid types. Let the API validate, don't duplicate validation logic.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pagination loop | Custom pagination in each method | `_paginated_fetch` helper | DRYs up offset/limit/total logic |
| List endpoint | Custom HTTP calls | `ListableResource.list()` | Standard v1 list is exactly the base class pattern |
| Detail endpoint | Custom HTTP calls | `GettableResource.get()` | Standard detail is exactly the base class pattern |

**Key insight:** The only custom code needed is path construction for `list_by_type` and wiring `_paginated_fetch` for `list_v2`. Everything else is inherited.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Date Parameters Are Unix Timestamps
**What goes wrong:** Passing ISO date strings to `startDate`/`endDate` → API returns 422 validation error.
**Why it happens:** Most modern APIs use ISO 8601, but Sonny's uses Unix timestamps (seconds since epoch).
**How to avoid:** Document that `startDate` and `endDate` expect Unix timestamps (type: number). Example: `client.transactions.list(startDate=1591040159, endDate=1595187359)`.
**Warning signs:** PayloadValidationError from the API.

### Pitfall 2: v2 Endpoint Has 10-Minute Response Cache
**What goes wrong:** Same reporting criteria within 10 minutes returns cached results, not fresh data.
**Why it happens:** API-side caching for performance — documented in the spec.
**How to avoid:** This is expected behavior, not a bug. Document it for consumers. No client-side mitigation needed.
**Warning signs:** Results don't change when re-querying immediately.

### Pitfall 3: Transaction Detail Response Wrapper Differs from List
**What goes wrong:** Trying to access `data.transactions` on a detail response → KeyError.
**Why it happens:** List endpoints return `{ data: { transactions: [...], total, offset, limit } }`. Detail endpoint returns `{ data: { id, number, type, ... } }` — the object directly, no array wrapper.
**How to avoid:** `GettableResource.get()` already handles this correctly (accesses `data` directly).
**Warning signs:** N/A — already handled by framework.

### Pitfall 4: item_type Path Param Uses Kebab-Case
**What goes wrong:** Passing `prepaid_wash` or `PrepaidWash` → 404.
**Why it happens:** The API uses kebab-case path values: `prepaid-wash`, `house-account`.
**How to avoid:** Accept the value as-is (string) and let the API validate. Document valid values.
**Warning signs:** EntityNotFoundError from the API.
</common_pitfalls>

<code_examples>
## Code Examples

### Endpoint Summary Table

| Endpoint | Method | Path | Query Params | Response Items Key | Model | Paginated |
|----------|--------|------|-------------|-------------------|-------|-----------|
| List (v1) | GET | `/transaction` | startDate, endDate, site, region, limit, offset | `transactions` | `TransactionListItem` | Yes |
| By Type | GET | `/transaction/type/{item_type}` | startDate, endDate, site, region, limit, offset | `transactions` | `TransactionListItem` | Yes |
| Detail | GET | `/transaction/{trans_id}` | (none) | N/A (direct object) | `Transaction` | No |
| List (v2) | GET | `/transaction/version-2` | startDate, endDate, site, region, limit, offset | `transactions` | `TransactionV2ListItem` | Yes |

### Response Shape: List Endpoints (v1 and by-type)
```json
{
  "data": {
    "transactions": [
      { "transNumber": 253425, "transId": "876:1001", "total": 7.99, "date": "2018-05-19T05:32:32.000Z" }
    ],
    "offset": 0,
    "limit": 10,
    "total": 22
  }
}
```

### Response Shape: v2 List
```json
{
  "data": {
    "transactions": [
      {
        "transNumber": 253425, "transId": "876:1001", "total": 7.99, "date": "2018-05-19T05:32:32.000Z",
        "customerId": "1:234",
        "isRecurringPlanSale": true,
        "isRecurringPlanRedemption": false,
        "transactionStatus": "Completed"
      }
    ],
    "offset": 0,
    "limit": 10,
    "total": 22
  }
}
```

### Response Shape: Detail
```json
{
  "data": {
    "id": "876:1001",
    "number": 253425,
    "type": "Sale",
    "completeDate": "2020-05-19T05:32:32.000Z",
    "locationCode": "SITE1",
    "salesDeviceName": "POS1",
    "total": 7.99,
    "tenders": [...],
    "items": [...],
    "discount": [...],
    "isRecurringPayment": false,
    "isRecurringRedemption": false,
    "isRecurringSale": false,
    "isPrepaidRedemption": false,
    "isPrepaidSale": false
  }
}
```

### Valid item_type Values for list_by_type
```
wash | prepaid-wash | recurring | washbook | giftcard | merchandise | house-account
```

### Query Parameters for All List Endpoints
```
startDate  — Unix timestamp (number), start of date range. Defaults to today.
endDate    — Unix timestamp (number), end of date range. Defaults to today.
site       — Site code string (e.g., "MAIN"). Overrides X-Sonnys-Site-Code header.
region     — Region code string (e.g., "NORTH"). Ignored if site is sent.
limit      — Page size, 1-100 (default 100).
offset     — Starting record, 1+ (default 1).
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

No ecosystem changes relevant to Phase 8 — this is internal API wrapping using established project patterns.

| Aspect | Status | Impact |
|--------|--------|--------|
| API version | v0.2.0 (pinned) | No changes expected |
| Transaction models | Built in Phase 4 | Ready to use as-is |
| Resource framework | Built in Phase 5 | Handles all standard patterns |
| `_paginated_fetch` helper | Built in Phase 7 | Pattern proven, ready to duplicate |

**Note on v2 vs v1:** The v2 endpoint adds `customerId`, `isRecurringPlanSale`, `isRecurringPlanRedemption`, and `transactionStatus` to the list item. It also has 10-minute server-side caching. This is the API's enhancement, not a breaking change — both endpoints remain available.
</sota_updates>

<open_questions>
## Open Questions

1. **Should `_paginated_fetch` be extracted to `BaseResource`?**
   - What we know: RecurringAccounts has it, Transactions will need it
   - What's unclear: Whether future resources will also need it
   - Recommendation: Duplicate for now (consistency), extract later if a third resource needs it

2. **TransactionListJobObject vs TransactionObject in get-job-data response**
   - What we know: The OpenAPI spec `get-job-data` response references `TransactionObject`, but a `TransactionListJobObject` schema exists that extends it
   - What's unclear: Which schema the API actually returns (spec may be inconsistent)
   - Recommendation: This is Phase 9's concern (batch job system). The `TransactionJobItem` model (built Phase 4) already extends `Transaction` to cover both.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `bo-data-open-api.yml` — Full OpenAPI spec for all transaction endpoints, parameters, and response schemas
- Existing codebase — `_resources.py`, `_transactions.py`, `_recurring.py`, `_client.py` — all established patterns

### Secondary (MEDIUM confidence)
- None needed — all information from primary sources

### Tertiary (LOW confidence)
- None
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Python SDK — resource class wrapping REST endpoints
- Ecosystem: None new — uses existing project infrastructure only
- Patterns: Path-param filtering, alternate list endpoints, shared query params
- Pitfalls: Unix timestamps, response caching, kebab-case enums

**Confidence breakdown:**
- Standard stack: HIGH — all components already built and tested
- Architecture: HIGH — follows proven patterns from Phases 5-7
- Pitfalls: HIGH — all from official OpenAPI spec
- Code examples: HIGH — response shapes from OpenAPI spec

**Research date:** 2026-02-10
**Valid until:** Indefinite (API pinned at v0.2.0, patterns established)
</metadata>

---

*Phase: 08-transaction-resources*
*Research completed: 2026-02-10*
*Ready for planning: yes*
