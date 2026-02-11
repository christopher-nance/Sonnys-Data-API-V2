# Stats

The **Stats** resource provides computed business analytics and KPIs derived
from transaction and recurring account data. Unlike other resources that wrap
REST endpoints directly, `client.stats` fetches raw data from the API and
aggregates it locally, giving you ready-to-use metrics like total sales, wash
volume, new memberships, and conversion rates without writing any aggregation
logic yourself.

## Choosing the Right Method

The stats resource offers six methods. Pick the one that matches your use case:

| Method | Returns | Description | API Calls |
|--------|---------|-------------|-----------|
| `total_sales(start, end)` | `SalesResult` | Revenue breakdown by category (recurring, retail) | 1 |
| `total_washes(start, end)` | `WashResult` | Wash volume breakdown (retail, prepaid) | 2 |
| `retail_wash_count(start, end)` | `int` | Count of retail wash transactions | 1 |
| `new_memberships_sold(start, end)` | `int` | Count of membership activations | 1 |
| `conversion_rate(start, end)` | `ConversionResult` | Membership conversion rate KPI | 2 |
| `report(start, end)` | `StatsReport` | All KPIs in a single call (most efficient) | 4 |

Use individual methods when you need a single metric. Use `report()` when you
need multiple KPIs -- it makes **4 API calls** instead of the **7** that would
result from calling the individual methods separately.

## Date Range Input

All stats methods accept a `start` and `end` parameter for the date range. You
can pass either an ISO-8601 date string or a Python `datetime` object:

```python
# ISO-8601 strings
result = client.stats.total_sales("2026-01-01", "2026-01-31")

# datetime objects
from datetime import datetime
result = client.stats.total_sales(
    datetime(2026, 1, 1),
    datetime(2026, 1, 31),
)
```

Naive datetime objects are assumed to be UTC. Timezone-aware datetimes are
preserved as-is. If `start` is after `end`, a `ValueError` is raised.

## Methods

### `total_sales(start, end) -> SalesResult`

Compute a revenue breakdown for a date range. Fetches all transactions via the
enriched v2 endpoint and categorizes them into three buckets: recurring plan
sales, recurring redemptions, and retail.

```python
result = client.stats.total_sales("2026-01-01", "2026-01-31")

print(f"Total revenue: ${result.total:.2f} ({result.count} transactions)")
print(f"Recurring plan sales: ${result.recurring_plan_sales:.2f} ({result.recurring_plan_sales_count})")
print(f"Recurring redemptions: ${result.recurring_redemptions:.2f} ({result.recurring_redemptions_count})")
print(f"Retail: ${result.retail:.2f} ({result.retail_count})")
```

**`SalesResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | `float` | Grand total revenue |
| `count` | `int` | Total transaction count |
| `recurring_plan_sales` | `float` | Revenue from recurring plan sales |
| `recurring_plan_sales_count` | `int` | Number of recurring plan sale transactions |
| `recurring_redemptions` | `float` | Revenue from recurring redemptions |
| `recurring_redemptions_count` | `int` | Number of recurring redemption transactions |
| `retail` | `float` | Revenue from retail transactions |
| `retail_count` | `int` | Number of retail transactions |

### `total_washes(start, end) -> WashResult`

Compute wash volume for a date range. Fetches transactions of type `"wash"`
(retail) and `"prepaid-wash"` (wash book redemptions) separately and returns
per-category counts and a combined total.

```python
result = client.stats.total_washes("2026-01-01", "2026-01-31")

print(f"Total washes: {result.total}")
print(f"Retail washes: {result.wash_count}")
print(f"Prepaid washes: {result.prepaid_wash_count}")
```

**`WashResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Combined wash count (retail + prepaid) |
| `wash_count` | `int` | Retail wash transaction count |
| `prepaid_wash_count` | `int` | Prepaid wash redemption count |

### `retail_wash_count(start, end) -> int`

Count retail wash transactions for a date range. Returns the number of
standard single-use wash transactions (excludes prepaid wash book
redemptions).

```python
count = client.stats.retail_wash_count("2026-01-01", "2026-01-31")
print(f"Retail washes: {count}")
```

### `new_memberships_sold(start, end) -> int`

Count new membership activations for a date range. Fetches recurring account
status changes and counts transitions where the new status is `"Active"`. This
includes both brand-new sign-ups and reactivations of previously cancelled or
suspended memberships.

```python
count = client.stats.new_memberships_sold("2026-01-01", "2026-01-31")
print(f"New memberships sold: {count}")
```

### `conversion_rate(start, end) -> ConversionResult`

Compute the membership conversion rate for a date range. Measures how
effectively a site converts retail wash customers into membership sign-ups. The
rate is computed as `new_memberships / total_opportunities` where total
opportunities is the sum of new membership activations and retail wash
transactions.

```python
result = client.stats.conversion_rate("2026-01-01", "2026-01-31")

print(f"Conversion rate: {result.rate:.1%}")
print(f"New memberships: {result.new_memberships}")
print(f"Retail washes: {result.retail_washes}")
print(f"Total opportunities: {result.total_opportunities}")
```

When there are zero opportunities the rate is `0.0` (division-by-zero safe).

**`ConversionResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `rate` | `float` | Conversion rate as a decimal (e.g. `0.15` = 15%) |
| `new_memberships` | `int` | Number of membership activations |
| `retail_washes` | `int` | Number of retail wash transactions |
| `total_opportunities` | `int` | Sum of new memberships and retail washes |

### `report(start, end) -> StatsReport`

Compute all KPIs for a date range in a single call. This is the most efficient
way to retrieve multiple stats -- it makes **4 API calls** and computes every
KPI locally, compared to the **7 API calls** that would result from calling
`total_sales()`, `total_washes()`, `new_memberships_sold()`, and
`conversion_rate()` individually.

```python
rpt = client.stats.report("2026-01-01", "2026-01-31")

print(f"Period: {rpt.period_start} to {rpt.period_end}")
print(f"Revenue: ${rpt.sales.total:.2f} ({rpt.sales.count} transactions)")
print(f"Washes: {rpt.washes.total} (retail: {rpt.washes.wash_count}, prepaid: {rpt.washes.prepaid_wash_count})")
print(f"New memberships: {rpt.new_memberships}")
print(f"Conversion rate: {rpt.conversion.rate:.1%}")
```

**`StatsReport` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `sales` | `SalesResult` | Revenue breakdown (see `total_sales()` above) |
| `washes` | `WashResult` | Wash volume breakdown (see `total_washes()` above) |
| `new_memberships` | `int` | Count of membership activations |
| `conversion` | `ConversionResult` | Conversion rate KPI (see `conversion_rate()` above) |
| `period_start` | `str` | ISO-8601 date string for start of report range |
| `period_end` | `str` | ISO-8601 date string for end of report range |

## Examples

### Monthly performance snapshot

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    rpt = client.stats.report("2026-01-01", "2026-01-31")

    print(f"January 2026 Performance")
    print(f"{'='*40}")
    print(f"Revenue:       ${rpt.sales.total:>10,.2f}")
    print(f"  Memberships: ${rpt.sales.recurring_plan_sales:>10,.2f}")
    print(f"  Retail:      ${rpt.sales.retail:>10,.2f}")
    print(f"Washes:        {rpt.washes.total:>10,}")
    print(f"New members:   {rpt.new_memberships:>10,}")
    print(f"Conversion:    {rpt.conversion.rate:>9.1%}")
```

### Compare two periods

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    jan = client.stats.report("2026-01-01", "2026-01-31")
    feb = client.stats.report("2026-02-01", "2026-02-28")

    rev_change = feb.sales.total - jan.sales.total
    wash_change = feb.washes.total - jan.washes.total

    print(f"Revenue change: ${rev_change:+,.2f}")
    print(f"Wash volume change: {wash_change:+,}")
    print(f"Conversion: {jan.conversion.rate:.1%} -> {feb.conversion.rate:.1%}")
```

### Quick single-metric check

When you only need one number, use the individual methods to minimize API
calls:

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Just need revenue? 1 API call
    sales = client.stats.total_sales("2026-01-01", "2026-01-31")
    print(f"Revenue: ${sales.total:.2f}")

    # Just need wash count? 2 API calls
    washes = client.stats.total_washes("2026-01-01", "2026-01-31")
    print(f"Washes: {washes.total}")
```

## Performance Tips

!!! tip "Use `report()` when you need multiple KPIs"
    Calling `total_sales()`, `total_washes()`, `new_memberships_sold()`, and
    `conversion_rate()` individually results in **7 API calls** because some
    underlying data fetches overlap. The `report()` method shares data fetches
    across KPIs and computes everything in just **4 API calls**:

    1. `transactions.list_v2()` -- used for sales breakdown
    2. `transactions.list_by_type("wash")` -- used for wash count and conversion rate
    3. `transactions.list_by_type("prepaid-wash")` -- used for prepaid wash count
    4. `recurring.list_status_changes()` -- used for new memberships and conversion rate

!!! tip "Use individual methods for single metrics"
    If you only need one stat, calling the individual method is more efficient
    than `report()`. For example, `retail_wash_count()` makes just **1 API
    call**, while `report()` always makes 4.

!!! note "No caching between calls"
    Stats methods do not cache results between calls. Each invocation fetches
    fresh data from the API. If you need the same stats multiple times, store
    the result in a variable rather than calling the method again.
