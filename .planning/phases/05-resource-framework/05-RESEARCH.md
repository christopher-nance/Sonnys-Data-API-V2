# Phase 5: Resource Framework - Research

**Researched:** 2026-02-10
**Domain:** Python API client resource pattern with auto-pagination
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Sonny's Data API response envelope structure and pagination contract to inform the base resource class design. This is a commodity Python SDK pattern — no external ecosystem research needed.

Key finding: The API uses a consistent paginated envelope `{"data": {"<items_key>": [...], "offset": int, "limit": int, "total": int}}` across all list endpoints, but the items key name varies per endpoint (e.g., `items`, `customers`, `transactions`, `accounts`). Two endpoints break the pattern: `/site/list` has no pagination, and `/employee` has pagination metadata in the response but accepts no limit/offset query parameters.

**Primary recommendation:** Build a base resource class with configurable items key and model class. Auto-pagination loops offset in increments of limit until offset >= total. Each resource subclass declares its path, items key, model type, and available methods (list, get, or both).
</research_summary>

<api_contract>
## API Response Contract

### Envelope Patterns

**1. Paginated list** — Most list endpoints:
```json
{
  "data": {
    "<items_key>": [ ... ],
    "offset": 0,
    "limit": 100,
    "total": 247
  }
}
```

**2. Non-paginated list** — Site only:
```json
{
  "data": {
    "sites": [ ... ]
  }
}
```

**3. Detail (single object)** — All get-by-ID endpoints:
```json
{
  "data": { ... }
}
```

**4. Batch job (Phase 9)** — Transaction job system:
```json
// POST /transaction/load-job → {"data": {"hash": "abc123"}}
// GET /transaction/get-job-data →
{
  "data": {
    "hash": "abc123",
    "status": "pass|working|fail",
    "data": [ ... ],
    "offset": 0, "limit": 100, "total": 50
  }
}
```

### Pagination Parameters

| Parameter Type | Limit Range | Offset Min | Used By |
|---------------|-------------|------------|---------|
| CollectionLimitParameter | 1–100 | 1 | Most list endpoints |
| CollectionLimitParameterV2 | 100–1000 | 1 | `/recurring-status` |
| CollectionSalesAdvisorLimitParameter | 1–500 | 1 | `/sales-outcome/list` |
| None (no pagination) | N/A | N/A | `/site/list`, `/employee` |

**Offset behavior:** Parameter minimum is 1 (per OpenAPI spec), but response examples show `"offset": 0`. When `offset > total`, items array is empty.

### Items Key Mapping (Critical for Resource Framework)

| Endpoint | Path | Items Key | List Model | Detail Model |
|----------|------|-----------|------------|--------------|
| Items | `/item` | `items` | `Item` | — |
| Transactions | `/transaction` | `transactions` | `TransactionListItem` | — |
| Transactions (by type) | `/transaction/type/{type}` | `transactions` | `TransactionListItem` | — |
| Transaction V2 | `/transaction/version-2` | `transactions` | `TransactionV2ListItem` | — |
| Transaction detail | `/transaction/{trans_id}` | — | — | `Transaction` |
| Customers | `/customer` | `customers` | `CustomerListItem` | — |
| Customer detail | `/customer/{customer_id}` | — | — | `Customer` |
| Employees | `/employee` | `employees` | `EmployeeListItem` | — |
| Employee detail | `/employee/{employee_id}` | — | — | `Employee` |
| Employee clock | `/employee/{id}/clock-entries` | — (special) | — | — (nested weeks) |
| Giftcards | `/giftcard-liablilty` | `giftcards` | `GiftcardListItem` | — |
| Washbooks | `/washbook/account/list` | `accounts` | `WashbookListItem` | — |
| Washbook detail | `/washbook/account/{id}/detail` | — | — | `Washbook` |
| Recurring | `/recurring` | `accounts` | `RecurringListItem` | — |
| Recurring detail | `/recurring/account/{id}/detail` | — | — | `Recurring` |
| Recurring status | `/recurring-status` | `accounts` | `RecurringStatusChange` | — |
| Recurring mods | `/recurring-modification` | `accounts` | `RecurringModification` | — |
| Recurring details list | `/recurring/account/details/list` | `accounts` | `Recurring` | — |
| Sites | `/site/list` | `sites` | `Site` | — |
| Sales advisor | `/sales-outcome/list` | `sales` | (no model yet) | — |

**Note:** `/giftcard-liablilty` is intentionally misspelled in the API (it's "liability" but the endpoint path is "liablilty").

### Special Endpoint Behaviors

1. **Employee list** — Has pagination in response but NO limit/offset query params. Returns all employees.
2. **Site list** — Explicitly "does not paginate." Returns all sites. Response has no offset/limit/total.
3. **Recurring status** — Uses V2 limit (100–1000) instead of standard (1–100).
4. **Employee clock entries** — Unique nested structure with weeks array containing clock entries. Max 14-day date range.
5. **Batch job** — Two-step: POST to get hash, GET to poll results. Status cycles: working → pass/fail. Data cached 20 min.
6. **Caching** — Some endpoints cache: `/item` (1 hour), `/transaction/version-2` (10 min), `/transaction/get-job-data` (20 min).
</api_contract>

<architecture_patterns>
## Architecture Patterns

### Recommended Resource Class Design

```python
class BaseResource:
    """Base class for all API resource classes."""

    def __init__(self, client: SonnysClient) -> None:
        self._client = client

class ListableResource(BaseResource):
    """Resource that supports list operations with auto-pagination."""

    _path: str           # e.g., "/customer"
    _items_key: str      # e.g., "customers"
    _model: type         # e.g., CustomerListItem
    _default_limit: int  # e.g., 100

class GettableResource(BaseResource):
    """Resource that supports get-by-ID operations."""

    _path: str           # e.g., "/customer"
    _model: type         # e.g., Customer
```

### Pattern: Descriptor-Based Resource Access

```python
class SonnysClient:
    @property
    def customers(self) -> CustomersResource:
        return CustomersResource(self)
```

Resources are lightweight — created on access, hold reference to client. No state.

### Pattern: Auto-Pagination Loop

```python
def list(self, **params) -> list[Model]:
    all_items = []
    offset = 1
    limit = self._default_limit

    while True:
        response = self._client._request("GET", self._path,
                                          params={"limit": limit, "offset": offset, **params})
        data = response.json()["data"]
        items = data[self._items_key]
        all_items.extend([self._model(**item) for item in items])

        total = data["total"]
        offset += limit
        if offset > total:
            break

    return all_items
```

### Pattern: Detail Endpoint

```python
def get(self, id: str) -> Model:
    response = self._client._request("GET", f"{self._path}/{id}")
    return self._model(**response.json()["data"])
```

### Anti-Patterns to Avoid
- **Caching in the client** — Out of scope per PROJECT.md ("always hits the API fresh")
- **Async support** — Out of scope per PROJECT.md ("synchronous only")
- **Generic T type parameter** — Overcomplicated for 8 resource types; just use concrete classes
</architecture_patterns>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Offset Confusion (0-based vs 1-based)
**What goes wrong:** Off-by-one in pagination loop causes duplicate or missing items
**Why it happens:** OpenAPI spec says offset minimum is 1, but response examples show offset: 0
**How to avoid:** Test with real API or use offset=1 as starting point (spec minimum). The auto-pagination loop should increment by limit each iteration.
**Warning signs:** First item duplicated, or one item missing between pages

### Pitfall 2: Items Key Varies Per Endpoint
**What goes wrong:** Hardcoding `data["items"]` fails for `/customer` (key is `customers`)
**Why it happens:** API uses different key names per resource type
**How to avoid:** Each resource class declares its `_items_key`. Base class uses it to extract array.
**Warning signs:** KeyError on first API call to a new resource

### Pitfall 3: Non-Paginated Endpoints in Pagination Loop
**What goes wrong:** Sending limit/offset to `/site/list` or `/employee` may cause errors or be silently ignored
**Why it happens:** Not all list endpoints accept pagination params
**How to avoid:** Flag non-paginated resources. Skip the pagination loop — just return the array directly.
**Warning signs:** Employee list always returns same results regardless of offset

### Pitfall 4: Rate Limiting During Auto-Pagination
**What goes wrong:** Fetching 1000+ items at limit=100 requires 10+ API calls, burning through rate limit
**Why it happens:** Auto-pagination makes many sequential requests
**How to avoid:** Rate limiter already built (Phase 3). The `_request` method handles this. No special pagination-level handling needed.
**Warning signs:** 429 errors during large list operations (handled by retry logic)

### Pitfall 5: Misspelled Endpoint Paths
**What goes wrong:** Using `/giftcard-liability` instead of `/giftcard-liablilty`
**Why it happens:** The API has a typo in the endpoint path
**How to avoid:** Use exact paths from OpenAPI spec. Document the misspelling.
**Warning signs:** 404 on giftcard list calls
</common_pitfalls>

<endpoint_classification>
## Endpoint Classification for Resource Classes

### Phase 5 Scope (Resource Framework)
- Base resource class with `_client` reference
- `list()` with auto-pagination loop
- `get()` for detail retrieval
- Non-paginated list handling

### Phase 6: Standard Resources
| Resource Class | list() | get() | Special |
|---------------|--------|-------|---------|
| `Customers` | `/customer` → `CustomerListItem[]` | `/customer/{id}` → `Customer` | Filters: firstName, lastName, status, dates, phone |
| `Items` | `/item` → `Item[]` | — | Filter: departmentName |
| `Employees` | `/employee` → `EmployeeListItem[]` | `/employee/{id}` → `Employee` | list() is non-paginated; clock entries are separate |
| `Sites` | `/site/list` → `Site[]` | — | Non-paginated, 1hr cache |

### Phase 7: Account Resources
| Resource Class | list() | get() | Special |
|---------------|--------|-------|---------|
| `Giftcards` | `/giftcard-liablilty` → `GiftcardListItem[]` | — | Misspelled path; filters: number, dates, site |
| `Washbooks` | `/washbook/account/list` → `WashbookListItem[]` | `/washbook/account/{id}/detail` → `Washbook` | Filters: dates, itemId, site |
| `Recurring` | `/recurring` → `RecurringListItem[]` | `/recurring/account/{id}/detail` → `Recurring` | Status history, modifications as sub-methods |

### Phase 8: Transaction Resources
| Resource Class | list() | get() | Special |
|---------------|--------|-------|---------|
| `Transactions` | `/transaction` → `TransactionListItem[]` | `/transaction/{id}` → `Transaction` | by_type(), v2_list(), dates/site/region filters |

### Phase 9: Batch Job System
| Resource | Method | Special |
|----------|--------|---------|
| `Transactions` | `batch()` | POST load-job → poll get-job-data → return results |
</endpoint_classification>

<open_questions>
## Open Questions

1. **Offset starting value**
   - What we know: OpenAPI spec says offset minimum is 1, but response examples show offset: 0
   - What's unclear: Whether first page should use offset=1 or offset=0
   - Recommendation: Start at offset=1 per spec minimum. Verify during integration testing (Phase 10).

2. **Employee list pagination**
   - What we know: Response includes offset/limit/total but endpoint accepts no pagination params
   - What's unclear: Does it always return all employees? Is total always equal to array length?
   - Recommendation: Treat as non-paginated. Return array directly without pagination loop.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `bo-data-open-api.yml` — OpenAPI 3.0 spec for the Sonny's Data API v0.2.0
- `.planning/PROJECT.md` — Project requirements and constraints
- `src/sonnys_data_client/_client.py` — Existing client implementation

### Secondary (MEDIUM confidence)
- None needed — all information from authoritative local sources

### Tertiary (LOW confidence)
- None
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Python resource pattern for REST API client
- Ecosystem: Internal design (pydantic, requests already chosen)
- Patterns: Resource class hierarchy, auto-pagination, response parsing
- Pitfalls: Offset indexing, key name variation, non-paginated endpoints

**Confidence breakdown:**
- API contract: HIGH — from OpenAPI spec
- Architecture: HIGH — standard Python SDK patterns
- Pitfalls: HIGH — derived from spec analysis
- Endpoint classification: HIGH — complete endpoint audit

**Research date:** 2026-02-10
**Valid until:** Indefinite (API pinned at v0.2.0, internal design patterns)
</metadata>

---

*Phase: 05-resource-framework*
*Research completed: 2026-02-10*
*Ready for planning: yes*
