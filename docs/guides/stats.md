# Stats

The **Stats** resource provides computed business analytics and KPIs derived
from transaction data. Unlike other resources that wrap REST endpoints
directly, `client.stats` fetches raw data from the API and aggregates it
locally, giving you ready-to-use metrics like total sales, wash volume, new
memberships, and conversion rates without writing any aggregation logic
yourself.

!!! note "Rinsed alignment"
    Stats calculations are designed to match **Rinsed** reporting as closely
    as possible.  Wash classification uses a combination of v2 transaction
    flags (`is_recurring_plan_sale`, `is_recurring_plan_redemption`) and v1
    type endpoints (`type=wash`, `type=recurring`) to accurately distinguish
    car washes from recharges and refunds.  In validation testing across 10
    days of JOLIET data, **7/10 days matched Rinsed exactly** on all wash
    metrics, with remaining days off by only 1-2 counts.

## Choosing the Right Method

The stats resource offers six methods. Pick the one that matches your use case:

| Method | Returns | Description | API Calls |
|--------|---------|-------------|-----------|
| `total_sales(start, end)` | `SalesResult` | Revenue breakdown by category (recurring, retail) | 1 |
| `total_washes(start, end)` | `WashResult` | Wash volume breakdown (member, retail, eligible, free) | 3 |
| `retail_wash_count(start, end)` | `int` | Count of retail wash transactions | 2 |
| `new_memberships_sold(start, end)` | `int` | Count of recurring plan sales | 1 |
| `conversion_rate(start, end)` | `ConversionResult` | Membership conversion rate KPI | 4 |
| `report(start, end)` | `StatsReport` | All KPIs in a single call (most efficient) | 3 |

Use individual methods when you need a single metric. Use `report()` when you
need multiple KPIs -- it makes **3 API calls** instead of the **11** that
would result from calling the individual methods separately.

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

Date-only strings automatically get boundary times applied (`00:00:01` start,
`23:59:59` end) in the site's local timezone, then converted to UTC.  Naive
datetime objects are assumed to be UTC.  Timezone-aware datetimes are converted
to UTC.  If `start` is after `end`, a `ValueError` is raised.

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

Compute wash volume for a date range. Uses three data sources to classify
transactions accurately:

- **v2 endpoint** -- provides `is_recurring_plan_sale` and `is_recurring_plan_redemption` flags
- **v1 `type=wash`** -- identifies actual car wash transactions
- **v1 `type=recurring`** -- identifies recharges (monthly billing) to exclude

Classification priority: redemption > plan sale > wash > recharge > unknown.
Transactions in both `type=wash` and `type=recurring` are treated as washes.
Negative-total transactions (refunds) are excluded entirely.

```python
result = client.stats.total_washes("2026-01-01", "2026-01-31")

print(f"Total washes: {result.total}")
print(f"Member washes: {result.member_wash_count}")
print(f"Retail washes: {result.retail_wash_count}")
print(f"Eligible washes: {result.eligible_wash_count}")
print(f"Free washes: {result.free_wash_count}")
```

**`WashResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Total wash count (member + retail + plan sale washes) |
| `member_wash_count` | `int` | Membership redemption washes |
| `retail_wash_count` | `int` | Non-member washes (includes unknown non-negative types) |
| `eligible_wash_count` | `int` | Derived: `total - member - free`. Denominator for conversion rate |
| `free_wash_count` | `int` | Washes with `total == 0` (complimentary) |

### `retail_wash_count(start, end) -> int`

Count retail wash transactions for a date range. A retail wash is a `type=wash`
transaction that is neither a recurring plan sale nor a recurring redemption.

```python
count = client.stats.retail_wash_count("2026-01-01", "2026-01-31")
print(f"Retail washes: {count}")
```

### `new_memberships_sold(start, end) -> int`

Count new membership sales for a date range. Fetches v2 transactions and counts
those flagged as `is_recurring_plan_sale`. This captures both brand-new
sign-ups and reactivations -- any transaction where a recurring plan was sold.

```python
count = client.stats.new_memberships_sold("2026-01-01", "2026-01-31")
print(f"New memberships sold: {count}")
```

### `conversion_rate(start, end) -> ConversionResult`

Compute the membership conversion rate for a date range. Measures how
effectively a site converts eligible wash customers into membership sign-ups.
The rate is computed as `new_memberships / eligible_washes`.

Eligible washes are derived from total washes: `total - member - free`. This
includes retail washes with `total > 0`, plan sale washes, and unknown
non-negative transaction types.

```python
result = client.stats.conversion_rate("2026-01-01", "2026-01-31")

print(f"Conversion rate: {result.rate:.1%}")
print(f"New memberships: {result.new_memberships}")
print(f"Eligible washes: {result.eligible_washes}")
```

When there are zero eligible washes the rate is `0.0` (division-by-zero safe).

**`ConversionResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `rate` | `float` | Conversion rate as a decimal (e.g. `0.15` = 15%) |
| `new_memberships` | `int` | Number of recurring plan sales |
| `eligible_washes` | `int` | Eligible washes (denominator) |

### `report(start, end) -> StatsReport`

Compute all KPIs for a date range in a single call. This is the most efficient
way to retrieve multiple stats -- it makes **3 API calls** and computes every
KPI locally, compared to the **11 API calls** that would result from calling
`total_sales()`, `total_washes()`, `new_memberships_sold()`, and
`conversion_rate()` individually.

```python
rpt = client.stats.report("2026-01-01", "2026-01-31")

print(f"Period: {rpt.period_start} to {rpt.period_end}")
print(f"Revenue: ${rpt.sales.total:.2f} ({rpt.sales.count} transactions)")
print(f"Washes: {rpt.washes.total} (member: {rpt.washes.member_wash_count}, retail: {rpt.washes.retail_wash_count})")
print(f"Eligible: {rpt.washes.eligible_wash_count}, Free: {rpt.washes.free_wash_count}")
print(f"New memberships: {rpt.new_memberships}")
print(f"Conversion rate: {rpt.conversion.rate:.1%}")
```

**`StatsReport` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `sales` | `SalesResult` | Revenue breakdown (see `total_sales()` above) |
| `washes` | `WashResult` | Wash volume breakdown (see `total_washes()` above) |
| `new_memberships` | `int` | Count of recurring plan sales |
| `conversion` | `ConversionResult` | Conversion rate KPI (see `conversion_rate()` above) |
| `period_start` | `str` | ISO-8601 date string for start of report range |
| `period_end` | `str` | ISO-8601 date string for end of report range |

## Examples

### Monthly performance snapshot

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key",
                   site_code="JOLIET") as client:
    rpt = client.stats.report("2026-01-01", "2026-01-31")

    print(f"January 2026 Performance")
    print(f"{'='*40}")
    print(f"Revenue:       ${rpt.sales.total:>10,.2f}")
    print(f"  Memberships: ${rpt.sales.recurring_plan_sales:>10,.2f}")
    print(f"  Retail:      ${rpt.sales.retail:>10,.2f}")
    print(f"Washes:        {rpt.washes.total:>10,}")
    print(f"  Member:      {rpt.washes.member_wash_count:>10,}")
    print(f"  Eligible:    {rpt.washes.eligible_wash_count:>10,}")
    print(f"  Free:        {rpt.washes.free_wash_count:>10,}")
    print(f"New members:   {rpt.new_memberships:>10,}")
    print(f"Conversion:    {rpt.conversion.rate:>9.1%}")
```

### Compare two periods

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key",
                   site_code="JOLIET") as client:
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

with SonnysClient(api_id="your-api-id", api_key="your-api-key",
                   site_code="JOLIET") as client:
    # Just need revenue? 1 API call
    sales = client.stats.total_sales("2026-01-01", "2026-01-31")
    print(f"Revenue: ${sales.total:.2f}")

    # Just need wash count? 3 API calls
    washes = client.stats.total_washes("2026-01-01", "2026-01-31")
    print(f"Washes: {washes.total}")
```

## Performance Tips

!!! tip "Use `report()` when you need multiple KPIs"
    Calling `total_sales()`, `total_washes()`, `new_memberships_sold()`, and
    `conversion_rate()` individually results in **11 API calls** because some
    underlying data fetches overlap. The `report()` method shares data fetches
    across KPIs and computes everything in just **3 API calls**:

    1. `transactions.list_v2()` -- enriched transactions with membership flags
    2. `transactions.list_by_type("wash")` -- identifies actual car washes
    3. `transactions.list_by_type("recurring")` -- identifies recharges to exclude

!!! tip "Use individual methods for single metrics"
    If you only need one stat, calling the individual method is more efficient
    than `report()`. For example, `total_sales()` makes just **1 API call**,
    while `report()` always makes 3.

!!! note "No caching between calls"
    Stats methods do not cache results between calls. Each invocation fetches
    fresh data from the API. If you need the same stats multiple times, store
    the result in a variable rather than calling the method again.
