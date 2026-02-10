# Phase 9: Batch Job System - Research

**Researched:** 2026-02-10
**Domain:** REST API async job polling pattern (submit job → poll for completion → retrieve paginated results)
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Sonny's Data API batch job endpoints (`/transaction/load-job` and `/transaction/get-job-data`) to understand the exact request/response contract, job lifecycle, and how to implement an auto-polling wrapper within the existing `Transactions` resource class.

The batch job system follows a standard async job pattern: POST reporting criteria to `load-job`, receive a hash, then poll `get-job-data` with that hash until the status transitions from `"working"` to `"pass"` (data ready) or `"fail"` (job failed). The response uses the same `TransactionObject` schema as the detail endpoint, already modeled as `TransactionJobItem`.

Key finding: The existing codebase already has everything needed — `_request()` supports POST, `TransactionJobItem` model exists, and the `Transactions` resource class is the natural home. The only new capability is the poll loop itself, which is a simple `time.sleep` pattern requiring no external dependencies.

**Primary recommendation:** Add `load_job()` method to the existing `Transactions` resource that handles the full submit → poll → paginate → return flow, with configurable `poll_interval` and `timeout` parameters.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | >=2.28,<3 | HTTP client (already a dependency) | `_request()` supports POST with query params out of the box |
| pydantic | >=2.10,<3 | Response models (already a dependency) | `TransactionJobItem` model already exists |
| time | stdlib | `time.sleep` + `time.monotonic` for polling | Standard library, no external deps needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none needed) | — | — | No additional dependencies required |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual poll loop | polling2 library | Adds a dependency for a ~15-line loop — not worth it |
| time.sleep | threading.Event.wait | Would enable cancellation but adds complexity; synchronous-only scope doesn't need it |
| time.time | time.monotonic | monotonic already used by rate limiter — immune to clock drift (prior decision from Phase 3) |

**Installation:**
```bash
# No new packages needed — all capabilities exist in current dependencies
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Where It Lives: Extend Existing `Transactions` Resource

The batch job methods belong on the existing `Transactions` resource class, not a new resource class. Rationale:
- The API endpoints are under `/transaction/` namespace
- The Transactions resource already has custom methods (`list_by_type`, `list_v2`, `_paginated_fetch`)
- Users expect `client.transactions.load_job()` not `client.batch_jobs.load_job()`
- `TransactionJobItem` model is already in `types/_transactions.py`

```
src/sonnys_data_client/
├── resources/
│   └── _transactions.py      # ADD: load_job() method here
└── types/
    └── _transactions.py       # EXISTING: TransactionJobItem already defined
```

### Pattern 1: Submit-Poll-Return (Single Method)

**What:** One method that handles the full lifecycle: submit job → poll until done → return results
**When to use:** Default pattern — caller just wants data, doesn't care about polling internals

```python
def load_job(
    self,
    *,
    poll_interval: float = 2.0,
    timeout: float = 300.0,
    **params: object,
) -> list[TransactionJobItem]:
    """Submit a batch job and poll until results are ready.

    Args:
        poll_interval: Seconds between poll attempts (default 2s).
        timeout: Max seconds to wait for job completion (default 300s / 5 min).
        **params: Query parameters (startDate, endDate, site, etc.).

    Returns:
        A list of TransactionJobItem instances.

    Raises:
        TimeoutError: If job doesn't complete within timeout.
        ServerError: If job status is "fail".
    """
    # Step 1: Submit job
    response = self._client._request("POST", "/transaction/load-job", params=params)
    hash_value = response.json()["data"]["hash"]

    # Step 2: Poll until complete
    deadline = time.monotonic() + timeout
    while True:
        response = self._client._request(
            "GET", "/transaction/get-job-data", params={"hash": hash_value}
        )
        body = response.json()["data"]
        status = body["status"]

        if status == "pass":
            # Step 3: Parse results
            return [TransactionJobItem.model_validate(item) for item in body["data"]]

        if status == "fail":
            raise ...  # Appropriate error

        # status == "working"
        if time.monotonic() >= deadline:
            raise ...  # Timeout error

        time.sleep(poll_interval)
```

### Pattern 2: Two-Phase API (Advanced Use)

**What:** Separate `submit_job()` and `get_job_data()` methods for callers who want manual control
**When to use:** When caller needs to submit multiple jobs, do other work, then collect results
**Decision:** DEFER — implement only if needed. The single-method pattern covers the PROJECT.md requirement ("Auto-polling for batch job endpoints — load-job → poll → return simplifies the most complex API pattern").

### Anti-Patterns to Avoid
- **Separate BatchJobs resource class:** The endpoints are `/transaction/*` — splitting them into a new resource confuses the API surface
- **Recursive polling:** Don't use recursion for the poll loop — stack depth grows with long jobs
- **No timeout:** Always require a timeout to prevent infinite loops on stuck jobs
- **Polling without rate limit awareness:** Each poll hits `_request()` which goes through the rate limiter — the poll loop must not starve other concurrent requests
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting during polls | Custom rate tracking in poll loop | Existing `_request()` with `RateLimiter` | Every poll call goes through `_request()` which already enforces 20 req/15s |
| 429 retry during polls | Custom retry in poll loop | Existing `_request()` retry logic | `_request()` already handles 429 with exponential backoff |
| Timeout tracking | `time.time()` with manual checks | `time.monotonic()` with deadline pattern | `time.monotonic()` is immune to system clock changes (Phase 3 decision) |
| Job status → exception mapping | Custom if/else chains | Reuse existing `make_status_error()` or raise `ServerError` | Keep error handling consistent with rest of client |
| TransactionJobItem model | New model definition | Existing `TransactionJobItem` in `types/_transactions.py` | Already defined in Phase 4, extends `Transaction` with v2-style fields |

**Key insight:** The entire polling infrastructure already exists in the codebase. The only new code is the poll loop itself (~20 lines) and the method signature. Everything else — HTTP requests, rate limiting, retries, error mapping, response models — is already built.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Rate Limiter Starvation During Polling
**What goes wrong:** Poll loop consumes all 20 req/15s slots, blocking other concurrent requests from the same client instance
**Why it happens:** Default poll_interval of 1s would burn through 15 requests in 15 seconds
**How to avoid:** Default poll_interval of 2.0s means ~7-8 polls per 15s window, leaving capacity for other operations. Document that aggressive poll intervals can starve the rate limiter.
**Warning signs:** Other requests from the same client start sleeping on rate limit during a poll loop

### Pitfall 2: Hash Expiry (20-Minute TTL)
**What goes wrong:** Job completes but caller doesn't retrieve data in time — hash expires, get-job-data returns 404
**Why it happens:** API caches job data for only 20 minutes. If timeout is set too high or processing takes too long, the window closes.
**How to avoid:** Default timeout of 300s (5 min) is well within the 20-minute cache window. Document the 20-minute cache TTL for callers who do manual polling.
**Warning signs:** `NotFoundError` from `get-job-data` after a previously successful `load-job`

### Pitfall 3: load-job Uses POST, Not GET
**What goes wrong:** Sending GET to `/transaction/load-job` may fail or behave unexpectedly
**Why it happens:** The OpenAPI spec declares it as `post:`, but the PHP example code shows `$client->request('GET', ...)`. The spec and example contradict each other.
**How to avoid:** Follow the OpenAPI spec (`POST`). If POST fails in testing, fall back to GET. Document the discrepancy.
**Warning signs:** Unexpected error response from load-job

### Pitfall 4: Pagination Ambiguity in get-job-data
**What goes wrong:** Response includes `offset`, `limit`, `total` fields but get-job-data only documents `hash` as an input parameter
**Why it happens:** OpenAPI spec may be incomplete — get-job-data might accept undocumented limit/offset query params
**How to avoid:** Start without pagination on get-job-data (assume all data comes in one response per the spec). The load-job endpoint accepts limit/offset which likely controls the batch size. If total > limit in the response, test whether passing limit/offset to get-job-data works.
**Warning signs:** Truncated results where `total` > length of `data` array in get-job-data response

### Pitfall 5: 24-Hour Date Range Limit
**What goes wrong:** load-job rejects requests with date ranges exceeding 24 hours
**Why it happens:** API doc states "the date range for reporting criteria can only be within a 24 hour time span"
**How to avoid:** Document the constraint in the method docstring. Don't try to auto-split larger ranges — let the caller manage this. The API will return a validation error that maps to `ValidationError`.
**Warning signs:** `ValidationError` from load-job when date range exceeds 24 hours
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from the OpenAPI spec and existing codebase:

### load-job Request/Response (from OpenAPI spec)
```python
# POST /transaction/load-job?startDate=1591040159&endDate=1591126559&site=MAIN&limit=100&offset=1
# Response 200:
{
    "data": {
        "hash": "1aabac6d068eef6a7bad3fdf50a05cc8"
    }
}
```

### get-job-data Request/Response (from OpenAPI spec)
```python
# GET /transaction/get-job-data?hash=1aabac6d068eef6a7bad3fdf50a05cc8
# Response 200 (job still working):
{
    "data": {
        "hash": "1aabac6d068eef6a7bad3fdf50a05cc8",
        "status": "working",
        "data": [],
        "offset": 0,
        "limit": 10,
        "total": 0
    }
}

# Response 200 (job complete):
{
    "data": {
        "hash": "1aabac6d068eef6a7bad3fdf50a05cc8",
        "status": "pass",
        "data": [
            {
                "id": "...",
                "number": 123,
                "type": "Sale",
                "completeDate": "...",
                "locationCode": "MAIN",
                "salesDeviceName": "POS-1",
                "total": 15.99,
                "tenders": [...],
                "items": [...],
                "discount": [],
                "isRecurringPayment": false,
                "isRecurringRedemption": false,
                "isRecurringSale": false,
                "isPrepaidRedemption": false,
                "isPrepaidSale": false,
                "customerId": "1:234",
                "isRecurringPlanSale": false,
                "isRecurringPlanRedemption": false,
                "transactionStatus": "Completed"
            }
        ],
        "offset": 0,
        "limit": 100,
        "total": 22
    }
}
```

### Existing _request() POST Support (from _client.py)
```python
# _request() already supports any HTTP method:
response = self._client._request("POST", "/transaction/load-job", params=params)
# The `params=` kwarg becomes query string parameters for both GET and POST
# Rate limiting and 429 retry apply automatically
```

### Existing TransactionJobItem Model (from types/_transactions.py)
```python
class TransactionJobItem(Transaction):
    """Transaction detail with v2-style enrichment fields.

    Returned by /transaction/get-job-data. Extends Transaction with
    customer_id, recurring plan flags, and transaction status.
    """
    customer_id: str | None = None
    is_recurring_plan_sale: bool
    is_recurring_plan_redemption: bool
    transaction_status: str
```

### Deadline Pattern (from existing rate_limiter.py)
```python
# Same time.monotonic() pattern used by the rate limiter:
import time

deadline = time.monotonic() + timeout
while time.monotonic() < deadline:
    # ... poll ...
    time.sleep(poll_interval)
raise TimeoutError(...)
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A | N/A | N/A | No ecosystem changes — this is a proprietary API with fixed spec |

**New tools/patterns to consider:**
- None — the Sonny's API is pinned at v0.2.0 and the client is synchronous-only

**Deprecated/outdated:**
- None — all patterns used are stable Python stdlib

**Note:** This phase is entirely about internal implementation against a fixed API. There are no ecosystem changes, library updates, or SOTA shifts to consider. The research value here is understanding the API contract, not discovering external tools.
</sota_updates>

<open_questions>
## Open Questions

1. **Does `get-job-data` accept undocumented `limit`/`offset` query params?**
   - What we know: Response includes `offset`, `limit`, `total` fields. But OpenAPI spec only lists `hash` as an input parameter.
   - What's unclear: Whether the API accepts pagination params on get-job-data, or if pagination is controlled entirely by the load-job call.
   - Recommendation: Implement without pagination on get-job-data first. If response shows `total` > `len(data)`, investigate by testing limit/offset params. The load-job endpoint already accepts limit/offset which likely controls batch size.

2. **Is `load-job` actually POST or GET?**
   - What we know: OpenAPI spec declares `post:`. PHP code example in the spec uses `$client->request('GET', ...)`.
   - What's unclear: Which one the server actually expects.
   - Recommendation: Use POST per the spec. If it fails during integration testing, switch to GET.

3. **What does `status: "fail"` include in the response?**
   - What we know: Status enum is `["pass", "working", "fail"]`. No separate error schema documented for the fail case.
   - What's unclear: Whether a fail response includes error details, or just `"status": "fail"` with empty data.
   - Recommendation: On `"fail"` status, raise `ServerError` with a descriptive message. If integration testing reveals error details in the response body, enhance the error message.

4. **Does the hash change when re-submitting identical criteria within 20 minutes?**
   - What we know: API doc says "if you input the exact reporting criteria within a 20 minute time frame, the API will not trigger a background process. Instead a hash will be returned."
   - What's unclear: Whether the returned hash is the same hash (cached) or a new one pointing to cached data.
   - Recommendation: Doesn't affect implementation — treat every hash as opaque. Document the 20-minute cache behavior in the docstring.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- OpenAPI spec `bo-data-open-api.yml` — `/transaction/load-job` endpoint definition (lines 2436-2514)
- OpenAPI spec `bo-data-open-api.yml` — `/transaction/get-job-data` endpoint definition (lines 2516-2612)
- OpenAPI spec `bo-data-open-api.yml` — `TransactionListJobObject` schema (lines 967-988)
- OpenAPI spec `bo-data-open-api.yml` — Parameter definitions: `TransactionHashParameter`, `TransactionStartDateParameter`, `TransactionEndDateParameter`, `TransactionSiteParameter`
- Existing codebase `src/sonnys_data_client/_client.py` — `_request()` method supporting POST with query params
- Existing codebase `src/sonnys_data_client/types/_transactions.py` — `TransactionJobItem` model
- Existing codebase `src/sonnys_data_client/resources/_transactions.py` — `Transactions` resource pattern

### Secondary (MEDIUM confidence)
- OpenAPI spec PHP code examples — show GET for load-job (contradicts spec's POST declaration)
- API description notes on caching (20-minute TTL) and date range limits (24-hour max)

### Tertiary (LOW confidence - needs validation)
- Pagination behavior of get-job-data — spec ambiguous, needs integration testing
- Exact behavior of status="fail" — no documented error response shape
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Sonny's Data API v0.2.0 batch job endpoints
- Ecosystem: No external libraries needed (all exists in current deps)
- Patterns: Submit-poll-return async job pattern, deadline-based timeout
- Pitfalls: Rate limiter starvation, hash expiry, POST/GET ambiguity, pagination gaps

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, everything already exists
- Architecture: HIGH - clear fit into existing Transactions resource
- Pitfalls: HIGH - derived from API spec constraints and existing codebase patterns
- Code examples: HIGH - from OpenAPI spec and existing codebase source

**Research date:** 2026-02-10
**Valid until:** 2026-03-12 (30 days - API is pinned at v0.2.0, no changes expected)
</metadata>

---

*Phase: 09-batch-job-system*
*Research completed: 2026-02-10*
*Ready for planning: yes*
