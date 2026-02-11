# Advanced Patterns

This guide covers SDK usage patterns that go beyond single-resource CRUD
operations. If you are building production data pipelines, operating across
multiple sites, or need to understand the rate limiter in depth, this is
the right place.

**Who this is for:**

- Developers building scheduled data pipelines that pull from multiple sites
- Operators managing separate databases (e.g., WashU and Icon) with different
  API credentials
- Anyone who needs to export large volumes of data efficiently without hitting
  rate limits

**Prerequisites:** Familiarity with the basic client usage covered in the
resource guides (e.g., [Transactions](transactions.md)) and the
[Error Handling guide](error-handling.md).

---

## Multi-Site Operations

The Sonny's API scopes data by site code. A single API ID may have access to
multiple sites, and an organization may operate multiple databases with
entirely separate credentials. This section covers patterns for working across
sites and databases.

### Single-Site vs Multi-Site Setup

When you pass `site_code` to the constructor, every request is scoped to that
site automatically via the `X-Sonnys-Site-Code` header:

```python
from sonnys_data_client import SonnysClient

# Scoped to a single site -- all requests return data for JOLIET only
with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code="JOLIET",
) as client:
    transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    print(f"Joliet transactions: {len(transactions)}")
```

Omitting `site_code` returns data for **all sites** the API ID has access to.
This is useful when you want a consolidated view without looping:

```python
# No site_code -- returns transactions across all authorized sites
with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
) as client:
    all_transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    print(f"All-site transactions: {len(all_transactions)}")
```

!!! tip
    Use `site_code` when you need per-site reporting or when the API ID has
    access to many sites and you want to reduce response size. Omit it when
    you need a quick cross-site total.

### Iterating Multiple Sites

When you need per-site breakdowns, create a separate client for each site
code. This is the standard pattern for daily dashboards and scheduled reports:

```python
from sonnys_data_client import SonnysClient

SITES = ["JOLIET", "ROMEOVILLE", "PLAINFIELD", "SHOREWOOD"]

daily_counts = {}

for site in SITES:
    with SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code=site,
    ) as client:
        transactions = client.transactions.list(
            startDate="2025-06-15",
            endDate="2025-06-16",
        )
        daily_counts[site] = len(transactions)

for site, count in daily_counts.items():
    print(f"{site}: {count} transactions")
```

!!! warning
    Each client in this loop shares the same `api_id`, which means the API
    server enforces a **single** 20 req/15s rate limit across all of them.
    See [Multi-Client Rate Limit Considerations](#multi-client-rate-limit-considerations)
    for details and mitigation strategies.

### Multi-Database Operations

Some organizations operate entirely separate databases with different API
credentials. For example, WashU and Icon each have their own `api_id` and
`api_key`. Create independent clients for each database:

```python
from sonnys_data_client import SonnysClient

# WashU database -- separate API credentials
washu_client = SonnysClient(
    api_id="washu-api-id",
    api_key="washu-api-key",
)

# Icon database -- separate API credentials
icon_client = SonnysClient(
    api_id="icon-api-id",
    api_key="icon-api-key",
)

try:
    washu_txns = washu_client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    icon_txns = icon_client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    print(f"WashU: {len(washu_txns)} transactions")
    print(f"Icon:  {len(icon_txns)} transactions")
    print(f"Combined: {len(washu_txns) + len(icon_txns)} transactions")
finally:
    washu_client.close()
    icon_client.close()
```

!!! note
    Since these clients use **different** API IDs, each has its own independent
    rate limit (20 req/15s per API ID). They will not interfere with each other.

### Consolidated Reporting

A common need is aggregating data across sites into a single report. This
pattern collects revenue per site for a date range and produces a summary:

```python
from sonnys_data_client import SonnysClient

SITES = ["JOLIET", "ROMEOVILLE", "PLAINFIELD", "SHOREWOOD"]

revenue_by_site = {}

for site in SITES:
    with SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code=site,
    ) as client:
        transactions = client.transactions.list(
            startDate="2025-06-01",
            endDate="2025-06-30",
        )
        revenue_by_site[site] = sum(txn.total for txn in transactions)

# Print consolidated report
total_revenue = sum(revenue_by_site.values())
print(f"{'Site':<15} {'Revenue':>12}")
print("-" * 28)
for site, revenue in revenue_by_site.items():
    pct = (revenue / total_revenue * 100) if total_revenue else 0
    print(f"{site:<15} ${revenue:>10,.2f}  ({pct:.1f}%)")
print("-" * 28)
print(f"{'TOTAL':<15} ${total_revenue:>10,.2f}")
```

Sample output:

```
Site                 Revenue
----------------------------
JOLIET          $  45,230.50  (32.1%)
ROMEOVILLE      $  38,910.25  (27.6%)
PLAINFIELD      $  31,445.00  (22.3%)
SHOREWOOD       $  25,310.75  (18.0%)
----------------------------
TOTAL           $ 140,896.50
```

!!! tip
    For large multi-site reports, add a `time.sleep(1)` between site iterations
    to avoid rate limit pressure. See
    [Request Spacing for Bulk Operations](#request-spacing-for-bulk-operations)
    for a configurable pattern.

### Context Managers for Multi-Site

When working with multiple clients simultaneously, use `contextlib.ExitStack`
to manage their lifecycles cleanly. This ensures all clients are closed even
if an error occurs partway through:

```python
import contextlib
from sonnys_data_client import SonnysClient

DATABASES = {
    "WashU": {"api_id": "washu-api-id", "api_key": "washu-api-key"},
    "Icon":  {"api_id": "icon-api-id",  "api_key": "icon-api-key"},
}

with contextlib.ExitStack() as stack:
    clients = {}
    for name, creds in DATABASES.items():
        client = SonnysClient(api_id=creds["api_id"], api_key=creds["api_key"])
        stack.enter_context(client)
        clients[name] = client

    # All clients are open -- use them freely
    for name, client in clients.items():
        sites = client.sites.list()
        print(f"{name}: {len(sites)} sites")

    # All clients are automatically closed when the block exits
```

For the common case of iterating sites within a single database, you can
combine `ExitStack` with site-scoped clients:

```python
import contextlib
from sonnys_data_client import SonnysClient

SITES = ["JOLIET", "ROMEOVILLE", "PLAINFIELD"]

with contextlib.ExitStack() as stack:
    clients = {}
    for site in SITES:
        client = SonnysClient(
            api_id="your-api-id",
            api_key="your-api-key",
            site_code=site,
        )
        stack.enter_context(client)
        clients[site] = client

    # Fetch data from all sites with all clients open
    for site, client in clients.items():
        txns = client.transactions.list(
            startDate="2025-06-15",
            endDate="2025-06-16",
        )
        print(f"{site}: {len(txns)} transactions")
```

!!! warning
    Opening multiple clients to the **same** API ID simultaneously means they
    all share the server-side rate limit but each has its own local rate
    limiter. The local limiters do not coordinate. If you fire requests from
    all clients at once, you will likely hit server-side 429s. Use sequential
    access or add delays between clients.

---

## Rate Limiting Deep Dive

The SDK includes a built-in rate limiter that prevents most 429 errors before
they happen. This section explains how the limiter works internally, what
happens with multiple clients, and how to forecast your request budget for
bulk operations.

For exception handling when rate limits are exceeded, see the
[Error Handling guide](error-handling.md#ratelimiterror).

### How the Rate Limiter Works

Each `SonnysClient` instance creates its own `RateLimiter` with a sliding
window algorithm:

- **Window:** 15 seconds (rolling, not fixed intervals)
- **Capacity:** 20 requests per window
- **Behavior:** The limiter tracks the timestamp of each request in a deque.
  Before every request, it purges timestamps older than 15 seconds. If fewer
  than 20 timestamps remain, the request proceeds immediately. If at capacity,
  the client **sleeps** until the oldest timestamp expires from the window.

```
Timeline (seconds):
0s    5s    10s   15s   20s   25s   30s
|-----|-----|-----|-----|-----|-----|
[  20 requests fired  ]
                       ^ window expires for req #1
                       ^ req #21 can now proceed
```

The key insight is that requests **never fail** due to the client-side rate
limiter. Instead, the client automatically waits until a slot opens. You can
observe this behavior by enabling debug logging:

```python
import logging
from sonnys_data_client import SonnysClient

logging.getLogger("sonnys_data_client").setLevel(logging.DEBUG)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # After 20 rapid requests, the 21st will pause automatically
    transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    # Debug log: "Rate limiter: waiting 2.350s"
```

!!! note
    The rate limiter is per-client-instance. Two separate `SonnysClient` objects
    each maintain independent rate limiters, even if they share the same
    `api_id`.

### Multi-Client Rate Limit Considerations

This is the most common source of unexpected 429 errors. Understanding it
will save you hours of debugging.

**The problem:** Each `SonnysClient` has its own local rate limiter allowing
20 req/15s. But the Sonny's API server enforces a **single** 20 req/15s limit
**per API ID**, regardless of how many clients use that ID. If two clients
share the same `api_id`, each thinks it can send 20 requests, but the server
only allows 20 total.

```
Client A (api_id="ABC"):  local limiter = 20 req/15s  ─┐
                                                         ├─> Server: 20 req/15s for "ABC"
Client B (api_id="ABC"):  local limiter = 20 req/15s  ─┘

Combined effective limit: 20 req/15s total, NOT 40
```

!!! warning "Shared API ID = shared rate limit"
    If you run N clients against the same `api_id`, expect effective per-client
    throughput of approximately **20/N requests per 15 seconds**. With 4
    site-scoped clients sharing one API ID, each client effectively gets
    ~5 req/15s before the server starts returning 429s.

The SDK handles server-side 429s with exponential backoff retries (up to
`max_retries` attempts), so your script will not crash immediately. But each
retry adds latency. It is faster to proactively space your requests than to
rely on retry-after-429 recovery.

**Mitigation strategies:**

1. **Sequential site iteration** -- Process one site at a time rather than
   opening all clients simultaneously (see
   [Iterating Multiple Sites](#iterating-multiple-sites)).

2. **Add delays between sites** -- Insert `time.sleep(2)` between site
   iterations to let the rate limit window recover.

3. **Increase `max_retries`** -- If you must run multiple clients concurrently,
   increase `max_retries` to give the backoff more room:

    ```python
    client = SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code="JOLIET",
        max_retries=5,  # More room for 429 recovery
    )
    ```

4. **Use separate API IDs** -- If available, request separate API credentials
   for separate processes. Each API ID gets its own 20 req/15s budget.

### Request Budget Forecasting

Before running a bulk export, estimate how many requests it will consume and
how long it will take. This helps you plan scheduling windows and avoid
surprises.

**Formula:** The API returns up to 100 records per page. For a paginated
endpoint:

```
pages = ceil(total_records / 100)
```

At 20 requests per 15 seconds, the minimum time to complete is:

```
time_seconds = (pages / 20) * 15
```

**Reference table:**

| Records | Pages | Min Time | Notes |
|--------:|------:|---------:|-------|
| 100 | 1 | < 1s | Single request |
| 500 | 5 | ~4s | Fits in one rate limit window |
| 1,000 | 10 | ~8s | Fits in one rate limit window |
| 2,000 | 20 | ~15s | Fills exactly one window |
| 5,000 | 50 | ~38s | ~2.5 windows |
| 10,000 | 100 | ~75s | 5 windows |
| 25,000 | 250 | ~188s (~3 min) | 12.5 windows |
| 50,000 | 500 | ~375s (~6 min) | 25 windows |

!!! note
    These estimates assume a single client with exclusive use of the API ID.
    If other processes share the same API ID, actual times will be longer due
    to contention.

**Example: estimating a monthly export**

```python
import math

# Estimate for a site that processes ~800 transactions per day
days_in_month = 30
daily_transactions = 800
total_records = days_in_month * daily_transactions  # 24,000

pages = math.ceil(total_records / 100)  # 240 pages
min_seconds = (pages / 20) * 15  # 180 seconds = 3 minutes

print(f"Estimated: {total_records:,} records, {pages} pages, ~{min_seconds:.0f}s")
```

!!! tip
    For `load_job()`, each page submits a separate batch job that must be
    polled. The total time includes polling delays (default 2s per poll).
    A 240-page `load_job()` export will take significantly longer than a
    240-page `list()` call. Use `list()` when you only need summary fields.

### Staying Within Limits

Practical tips to keep your scripts running smoothly without hitting rate
limits:

**1. Add sleep between site iterations**

```python
import time
from sonnys_data_client import SonnysClient

SITES = ["JOLIET", "ROMEOVILLE", "PLAINFIELD", "SHOREWOOD"]

for site in SITES:
    with SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code=site,
    ) as client:
        transactions = client.transactions.list(
            startDate="2025-06-15",
            endDate="2025-06-16",
        )
        print(f"{site}: {len(transactions)} transactions")

    time.sleep(2)  # Let the rate limit window recover between sites
```

**2. Use `load_job()` for bulk exports instead of paginated `list()`**

A `load_job()` call for 10,000 records uses fewer API requests than paginating
through `list()`, because the batch job server does the heavy lifting. The
tradeoff is wall-clock time (polling delay), but the request budget impact is
lower.

**3. Keep date ranges narrow**

Fewer records per query means fewer pages, which means fewer requests.
Day-by-day iteration is the safest approach for large exports:

```python
from datetime import date, timedelta
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    start = date(2025, 6, 1)
    end = date(2025, 6, 30)
    current = start

    while current < end:
        next_day = current + timedelta(days=1)
        transactions = client.transactions.list(
            startDate=current.isoformat(),
            endDate=next_day.isoformat(),
        )
        print(f"{current}: {len(transactions)} transactions")
        current = next_day
```

**4. Stagger scheduled jobs**

If you have multiple cron jobs or scheduled tasks using the same API ID,
offset their start times by at least 60 seconds. Two jobs starting
simultaneously will compete for the same 20 req/15s budget.

!!! tip
    The [Error Handling guide](error-handling.md#built-in-retry-behavior)
    covers what happens when rate limits are exceeded despite these
    precautions -- the SDK retries 429s with exponential backoff before
    raising `RateLimitError`.

---

## Performance Optimization

Getting data out of the API efficiently means choosing the right method,
sizing your date ranges, and spacing your requests. This section provides
practical guidance for minimizing wall-clock time and request budget usage
in production pipelines.

### Choosing the Right Method

The Transactions resource offers five methods, each with different performance
characteristics. The [Transactions guide](transactions.md#choosing-the-right-method)
has a full comparison table. Here is the decision from a **performance**
perspective:

| Priority | Method | Speed | Request Cost | Best For |
|:--------:|--------|-------|--------------|----------|
| 1 | `list()` | Fastest | 1 req per 100 records | Daily counts, revenue totals, date range summaries |
| 2 | `list_by_type()` | Fast | 1 req per 100 records | Type-filtered queries (fewer records = fewer pages) |
| 3 | `list_v2()` | Fast | 1 req per 100 records | When you need `customer_id` or recurring flags |
| 4 | `get()` | Per-record | 1 req per record | Single transaction detail lookup |
| 5 | `load_job()` | Slowest | Submit + poll + paginate | Bulk full-detail exports |

!!! tip "Default to `list()` unless you need specific fields"
    `list()` has no server-side caching layer and returns results immediately.
    It is the fastest method for most reporting use cases. Only switch to
    `list_v2()` when you specifically need `customer_id`,
    `is_recurring_plan_sale`, `is_recurring_plan_redemption`, or
    `transaction_status`. Only use `load_job()` when you need full transaction
    detail (tenders, line items, discounts) on every record.

**Avoid `get()` in loops.** Fetching 500 transactions one at a time with
`get()` costs 500 requests. The same data from `load_job()` costs roughly
5 job submissions + polling. If you need full detail on many transactions,
always prefer `load_job()`:

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # BAD: 500 requests for 500 transactions
    # for tid in transaction_ids:
    #     detail = client.transactions.get(tid)

    # GOOD: ~5 requests for 500 transactions with full detail
    results = client.transactions.load_job(
        startDate="2025-06-15",
        endDate="2025-06-16",
    )
```

### Date Range Sizing

Narrower date ranges mean fewer records per query, which means fewer pages and
fewer requests. The tradeoff is more iterations if you need a wide range.

**Guidelines by method:**

| Method | Recommended Range | Reason |
|--------|-------------------|--------|
| `list()` | Up to 30 days | Fast pagination, no caching complications |
| `list_v2()` | Up to 30 days | 10-min cache; repeated calls within cache window return stale data |
| `load_job()` | Exactly 1 day | **Required** -- max 24-hour range per call |

For `load_job()` exports spanning multiple days, iterate day by day. The
[Transactions guide](transactions.md#multi-day-exports) shows this pattern in
detail. Here is the performance-optimized version with request spacing:

```python
import time
from datetime import date, timedelta
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    start = date(2025, 6, 1)
    end = date(2025, 6, 30)
    all_results = []
    current = start

    while current < end:
        next_day = current + timedelta(days=1)
        day_results = client.transactions.load_job(
            startDate=current.isoformat(),
            endDate=next_day.isoformat(),
        )
        all_results.extend(day_results)
        print(f"{current}: {len(day_results)} transactions")
        current = next_day

        # Pause between days to stay well within rate limits
        time.sleep(1)

    print(f"Total: {len(all_results)} transactions over {(end - start).days} days")
```

!!! note
    For `list()` and `list_v2()`, wider date ranges are fine if you only need
    summary data. A 30-day `list()` query on a site with 800 transactions/day
    returns ~24,000 records across ~240 pages -- about 3 minutes of wall time
    with a single client.

### Request Spacing for Bulk Operations

Even though the SDK handles 429 retries automatically, each retry adds
latency. A request that gets a 429, waits 1 second, retries, and succeeds
takes ~1.7 seconds instead of ~0.7 seconds. Proactive spacing is faster
overall than reactive retry.

Here is a configurable pattern for bulk operations with built-in spacing:

```python
import time
from datetime import date, timedelta
from sonnys_data_client import SonnysClient

def export_site_transactions(
    api_id: str,
    api_key: str,
    site_code: str,
    start: date,
    end: date,
    delay_between_days: float = 1.0,
) -> list:
    """Export transactions for a site with configurable request spacing."""
    all_results = []

    with SonnysClient(
        api_id=api_id,
        api_key=api_key,
        site_code=site_code,
    ) as client:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            day_results = client.transactions.load_job(
                startDate=current.isoformat(),
                endDate=next_day.isoformat(),
            )
            all_results.extend(day_results)
            current = next_day

            if current < end:
                time.sleep(delay_between_days)

    return all_results


# Usage: export June for Joliet with 2-second spacing
results = export_site_transactions(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code="JOLIET",
    start=date(2025, 6, 1),
    end=date(2025, 6, 30),
    delay_between_days=2.0,
)
print(f"Exported {len(results)} transactions")
```

For multi-site exports, add an additional delay between sites:

```python
import time
from datetime import date

SITES = ["JOLIET", "ROMEOVILLE", "PLAINFIELD", "SHOREWOOD"]

for i, site in enumerate(SITES):
    results = export_site_transactions(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code=site,
        start=date(2025, 6, 1),
        end=date(2025, 6, 30),
        delay_between_days=1.0,
    )
    print(f"{site}: {len(results)} transactions")

    # Pause between sites (skip after the last one)
    if i < len(SITES) - 1:
        time.sleep(5)
```

!!! warning
    Do not set `delay_between_days` to 0 for large exports. While the SDK
    will handle the resulting 429s gracefully, the exponential backoff delays
    (1s, 2s, 4s per retry) will make the total run time **longer** than a
    small proactive delay would.

### Batch Jobs vs Paginated Lists

The choice between `load_job()` and `list()` is the most impactful performance
decision. Here is when to use each:

**Use `list()` when:**

- You need summary fields only (transaction number, total, date)
- You are building dashboards or real-time reports
- Speed matters more than data completeness
- You are querying across wide date ranges (up to 30 days)

**Use `load_job()` when:**

- You need full transaction detail (tenders, line items, discounts) on every
  record
- You need v2 enrichment fields (`customer_id`, `transaction_status`) combined
  with full detail
- You are building a data warehouse or archival export
- You can tolerate longer run times (polling overhead)

**Performance comparison for 1,000 transactions:**

| Aspect | `list()` | `load_job()` |
|--------|----------|--------------|
| Requests | 10 (paginated) | ~10 job submissions + ~10 poll cycles |
| Wall time | ~8 seconds | ~30-60 seconds (includes polling) |
| Data depth | Summary only | Full detail + v2 fields |
| Caching | None | 20-min server cache |

!!! note "Leveraging the `load_job()` cache"
    Job results are cached by the API for **20 minutes**. If you call
    `load_job()` with the same parameters within that window, the API returns
    cached results without re-processing the job. This means repeated calls
    are fast -- useful for retry-after-failure scenarios. See the
    [Transactions guide](transactions.md#batch-job-workflow) for details on the
    job lifecycle.

**Hybrid approach:** Use `list()` to get transaction counts and summaries,
then use `load_job()` only for the specific date ranges where you need full
detail:

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Step 1: Quick summary scan with list()
    summary = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    print(f"Found {len(summary)} transactions in June")

    # Step 2: Full detail export only for high-value days
    high_value_txns = [t for t in summary if t.total > 500]
    print(f"{len(high_value_txns)} high-value transactions to inspect")

    # Step 3: Get full detail for specific transactions
    for txn in high_value_txns[:10]:  # Limit to first 10
        detail = client.transactions.get(txn.trans_id)
        print(
            f"#{detail.number}: ${detail.total:.2f} - "
            f"{len(detail.items)} items, {len(detail.tenders)} tenders"
        )
```

---

## Integration Recipes

Ready-to-use patterns for the most common SDK integration scenarios. Each
recipe is a complete, copy-pasteable script that uses only the standard library
and the SDK itself -- no extra dependencies required. Change the credentials
and run.

### Export to CSV

Export transaction data for a date range to a CSV file. Uses `model_dump()`
to convert each Pydantic model to a dictionary, then writes rows with the
standard `csv` module.

```python
import csv
from sonnys_data_client import SonnysClient

with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code="JOLIET",
) as client:
    transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

if transactions:
    fieldnames = list(transactions[0].model_dump().keys())
    with open("joliet_transactions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for txn in transactions:
            writer.writerow(txn.model_dump())

    print(f"Exported {len(transactions)} transactions to joliet_transactions.csv")
```

!!! tip
    Use `list_v2()` instead of `list()` when you need enriched CSV exports
    with `customer_id`, `is_recurring_plan_sale`, `is_recurring_plan_redemption`,
    and `transaction_status` columns. Use `list()` for lightweight exports
    with just `trans_number`, `trans_id`, `total`, and `date`.

### Export to JSON

Export transaction data to a JSON file. Use `model_dump(mode="json")` to get
a JSON-serializable dictionary (handles dates, decimals, etc.).

```python
import json
from sonnys_data_client import SonnysClient

with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code="JOLIET",
) as client:
    transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

data = [txn.model_dump(mode="json") for txn in transactions]

with open("joliet_transactions.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Exported {len(data)} transactions to joliet_transactions.json")
```

!!! note
    Use `model_dump(mode="json", by_alias=True)` if the downstream consumer
    expects camelCase field names matching the raw API format (e.g.,
    `transNumber` instead of `trans_number`).

### Scheduled Daily Export

A script designed to run once per day that exports yesterday's transactions to
a date-stamped CSV file. Ideal for cron jobs or Windows Task Scheduler.

```python
"""daily_export.py -- Export yesterday's transactions to a date-stamped CSV."""
import csv
import logging
from datetime import date, timedelta
from pathlib import Path

from sonnys_data_client import SonnysClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

yesterday = date.today() - timedelta(days=1)
today = date.today()
output_dir = Path("exports")
output_dir.mkdir(exist_ok=True)
output_file = output_dir / f"transactions_{yesterday.isoformat()}.csv"

with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code="JOLIET",
) as client:
    transactions = client.transactions.list(
        startDate=yesterday.isoformat(),
        endDate=today.isoformat(),
    )

if transactions:
    fieldnames = list(transactions[0].model_dump().keys())
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for txn in transactions:
            writer.writerow(txn.model_dump())

logger.info("Exported %d transactions to %s", len(transactions), output_file)
```

!!! note "Scheduling this script"
    **Linux/Mac (cron):** Run daily at 6:00 AM:

    ```
    0 6 * * * python /path/to/daily_export.py
    ```

    **Windows (Task Scheduler):** Create a Basic Task triggered daily at
    6:00 AM, with the action "Start a program" pointing to your Python
    executable and the script path as the argument.

### Multi-Site Daily Report

Combine the multi-site iteration pattern with CSV export to produce either
per-site CSV files or a single consolidated CSV with a `site_code` column.
This example builds a consolidated file.

```python
"""multi_site_report.py -- Consolidated daily report across all sites."""
import csv
import time
from datetime import date, timedelta
from pathlib import Path

from sonnys_data_client import SonnysClient

SITES = ["JOLIET", "ROMEOVILLE", "PLAINFIELD", "SHOREWOOD"]

yesterday = date.today() - timedelta(days=1)
today = date.today()
output_file = Path(f"daily_report_{yesterday.isoformat()}.csv")

all_rows = []

for site in SITES:
    with SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code=site,
    ) as client:
        transactions = client.transactions.list(
            startDate=yesterday.isoformat(),
            endDate=today.isoformat(),
        )
        for txn in transactions:
            row = txn.model_dump()
            row["site_code"] = site
            all_rows.append(row)
    time.sleep(2)  # Respect shared rate limit between sites

if all_rows:
    fieldnames = list(all_rows[0].keys())
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

print(f"Exported {len(all_rows)} transactions across {len(SITES)} sites")
print(f"Output: {output_file}")
```

!!! tip
    For per-site CSV files instead of a consolidated file, move the file
    writing inside the site loop and use
    `Path(f"{site}_{yesterday.isoformat()}.csv")` as the output path. See
    [Iterating Multiple Sites](#iterating-multiple-sites) for the base pattern.

### Data Pipeline Pattern

A structured fetch-validate-transform-load pipeline. This example pulls
recurring account data, filters to active accounts, calculates key metrics
(active count, monthly recurring revenue), and writes a summary to JSON.

```python
"""recurring_pipeline.py -- Recurring account data pipeline."""
import json
import logging
from datetime import date
from pathlib import Path

from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Fetch ---
try:
    with SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        site_code="JOLIET",
    ) as client:
        accounts = client.recurring.list_details()
except APIError as e:
    logger.error("Failed to fetch recurring accounts: %s", e)
    raise SystemExit(1)

logger.info("Fetched %d recurring accounts", len(accounts))

# --- Validate & Transform ---
active = [a for a in accounts if a.current_recurring_status_name == "Active"]
mrr = sum(a.billing_amount for a in active if a.billing_amount is not None)

summary = {
    "date": date.today().isoformat(),
    "total_accounts": len(accounts),
    "active_accounts": len(active),
    "monthly_recurring_revenue": round(mrr, 2),
    "average_billing": round(mrr / len(active), 2) if active else 0,
}

# --- Load ---
output_file = Path(f"recurring_summary_{date.today().isoformat()}.json")
with open(output_file, "w") as f:
    json.dump(summary, f, indent=2)

logger.info("Pipeline complete: %d active accounts, MRR=$%.2f", len(active), mrr)
logger.info("Output: %s", output_file)
```

!!! tip
    For production pipelines, reference the
    [Error Handling guide](error-handling.md#retry-strategies) for more
    granular exception handling. You can wrap each pipeline stage in its own
    try/except to handle partial failures gracefully.

### Monitoring & Alerting Recipe

A simple script that checks a KPI (today's transaction count) against a
threshold and logs a warning when the value is below expected volume. Run this
on a schedule to catch low-volume days early.

```python
"""monitor_volume.py -- Check daily transaction volume against threshold."""
import logging
from datetime import date, timedelta

from sonnys_data_client import SonnysClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SITE = "JOLIET"
MIN_EXPECTED_TRANSACTIONS = 200  # Typical daily volume for this site

today = date.today()
yesterday = today - timedelta(days=1)

with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code=SITE,
) as client:
    transactions = client.transactions.list(
        startDate=yesterday.isoformat(),
        endDate=today.isoformat(),
    )

count = len(transactions)
revenue = sum(txn.total for txn in transactions)

logger.info("%s: %d transactions, $%.2f revenue", SITE, count, revenue)

if count < MIN_EXPECTED_TRANSACTIONS:
    logger.warning(
        "LOW VOLUME ALERT: %s had %d transactions (expected >= %d)",
        SITE, count, MIN_EXPECTED_TRANSACTIONS,
    )
else:
    logger.info("%s volume is normal (%d >= %d)", SITE, count, MIN_EXPECTED_TRANSACTIONS)
```

!!! tip "Extending with real alerts"
    This recipe logs warnings to stdout. In production, extend it with:

    - **Email alerts:** Use `smtplib` from the standard library to send an
      email when the threshold is breached.
    - **Slack webhooks:** Use `urllib.request` to POST a JSON payload to a
      Slack incoming webhook URL.
    - **Integration with the logging config** from the
      [Error Handling guide](error-handling.md#logging-configuration) to route
      warnings to a file or external logging service.
