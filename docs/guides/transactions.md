# Transactions

The **Transactions** resource provides access to transaction records across all
wash types. This is the most feature-rich resource in the client, offering five
methods including type-filtered listing, an enriched v2 endpoint, and a batch
job system for large exports. Use this resource to retrieve transaction
summaries, full details with tenders and line items, and bulk data exports.

## Choosing the Right Method

The Transactions resource exposes five methods. Use this table to pick the
right one for your use case:

| Method | Returns | Use When | Caching | Pagination |
|--------|---------|----------|---------|------------|
| `list()` | `TransactionListItem` | Quick summaries, date range queries | None | Auto |
| `list_by_type()` | `TransactionListItem` | Filtering by wash/prepaid/recurring/etc. | None | Auto |
| `list_v2()` | `TransactionV2ListItem` | Need customer_id, recurring flags, status | 10-min cache | Auto |
| `get()` | `Transaction` | Full detail for a single transaction | None | N/A |
| `load_job()` | `TransactionJobItem` | Bulk exports, full detail + v2 fields | 20-min cache | Auto (job-level) |

For most day-to-day queries, start with **`list()`** -- it is the fastest
method with no caching layer. Switch to **`list_by_type()`** when you only need
a specific transaction type (e.g., `"recurring"` or `"giftcard"`). Use
**`list_v2()`** when your analysis requires the enriched fields like
`customer_id`, `is_recurring_plan_sale`, or `transaction_status` -- but be aware
of the 10-minute cache. Call **`get()`** when you need the complete detail for a
single transaction, including tenders, line items, and discounts. For bulk
exports where you need full transaction detail on every record, use
**`load_job()`** -- it combines the depth of `get()` with the enrichment of
`list_v2()`, at the cost of a slower batch-job workflow and a 20-minute cache.

## Query Parameters

The list methods (`list()`, `list_by_type()`, `list_v2()`) and `load_job()` all
accept the same query parameters:

| Parameter   | Type         | Description                              |
|-------------|--------------|------------------------------------------|
| `startDate` | `str \| int` | Start of date range — ISO 8601 string (`"2026-01-15"`) or Unix timestamp (`1736899200`) |
| `endDate`   | `str \| int` | End of date range — ISO 8601 string (`"2026-01-31"`) or Unix timestamp (`1738281600`) |
| `site`      | `str`        | Filter by site code                      |
| `region`    | `str`        | Filter by region                         |

!!! note "Pagination is handled automatically"
    The `limit` and `offset` parameters are managed by the client's
    auto-pagination logic -- you do not need to set these manually. For
    `load_job()`, `limit` and `offset` control job-level pagination (default
    100 records per job page), but the client handles this transparently.

!!! info "Date conversion"
    The SDK automatically converts ISO 8601 date strings to Unix timestamps
    before sending them to the API. You can pass either format — the SDK
    handles the conversion transparently.

!!! info "`get()` takes no query parameters"
    The `get()` method accepts only a positional `trans_id` argument and does
    not support any query parameters. Pass the transaction ID directly:
    `client.transactions.get("98765")`.

## Methods

### `list(**params) -> list[TransactionListItem]`

Fetch all transactions. Returns a list of `TransactionListItem` objects with
summary fields. The client automatically paginates through all pages of results.

```python
transactions = client.transactions.list()
```

You can pass optional query parameters to filter results:

```python
transactions = client.transactions.list(
    startDate="2025-06-01",
    endDate="2025-06-30",
)
```

### `get(trans_id) -> Transaction`

Fetch full details for a single transaction by its ID. Returns a `Transaction`
object with tenders, line items, discounts, and employee information.

```python
transaction = client.transactions.get("98765")
```

### `list_by_type(item_type, **params) -> list[TransactionListItem]`

Fetch all transactions of a specific type. The `item_type` parameter accepts
these values:

- `wash` -- standard wash transactions
- `prepaid-wash` -- prepaid wash redemptions
- `recurring` -- recurring membership transactions
- `washbook` -- wash book transactions
- `giftcard` -- gift card transactions
- `merchandise` -- merchandise sales
- `house-account` -- house account transactions

```python
wash_transactions = client.transactions.list_by_type("wash")
```

### `list_v2(**params) -> list[TransactionV2ListItem]`

Fetch all transactions using the v2 endpoint. Returns enriched list items with
additional fields: `customer_id`, `is_recurring_plan_sale`,
`is_recurring_plan_redemption`, and `transaction_status`.

```python
transactions_v2 = client.transactions.list_v2(
    startDate="2025-06-01",
    endDate="2025-06-30",
)
```

!!! info "V2 caching"
    The API caches v2 responses for **10 minutes** per reporting criteria. If
    you need real-time data, use the standard `list()` method instead.

### `load_job(*, poll_interval=2.0, timeout=300.0, **params) -> list[TransactionJobItem]`

Submit a batch job and auto-poll until results are ready. Returns
`TransactionJobItem` objects -- full transaction details enriched with v2
fields. The method handles pagination at the job submission level, submitting
as many jobs as needed to retrieve all records.

```python
job_results = client.transactions.load_job(
    startDate="2025-06-15",
    endDate="2025-06-16",
    site="JOLIET",
)
```

!!! warning "Date range limit and site parameter"
    The `load_job()` method is limited to a **maximum 24-hour date range** per
    call. For longer periods, submit multiple jobs with consecutive date ranges.

    The `site` parameter is **required** for `load_job()` — pass it explicitly
    even if you set `site_code` on the client constructor.

!!! info "Job caching and polling"
    Job data is cached by the API for **20 minutes**. The `poll_interval`
    parameter controls how frequently the client checks for results (default
    2 seconds), and `timeout` sets the maximum wait time per job (default
    300 seconds / 5 minutes).

## Examples

### List transactions with date range

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    for txn in transactions:
        print(
            f"#{txn.trans_number} (ID: {txn.trans_id}) - "
            f"${txn.total:.2f} on {txn.date}"
        )
```

### Get transaction detail

The detail endpoint returns the complete transaction including tenders, line
items, discounts, and employee information:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    txn = client.transactions.get("98765")

    # Transaction summary
    print(f"Transaction #{txn.number} ({txn.type})")
    print(f"Date: {txn.complete_date}")
    print(f"Location: {txn.location_code}")
    print(f"Total: ${txn.total:.2f}")
    print(f"Customer: {txn.customer_name or 'N/A'}")
    print(f"Cashier: {txn.employee_cashier or 'N/A'}")

    # Line items
    print("\nItems:")
    for item in txn.items:
        voided = " [VOIDED]" if item.is_voided else ""
        print(f"  {item.name} ({item.department}): ${item.net:.2f}{voided}")

    # Payment tenders
    print("\nTenders:")
    for tender in txn.tenders:
        print(f"  {tender.tender}: ${tender.total:.2f}")

    # Discounts
    if txn.discounts:
        print("\nDiscounts:")
        for disc in txn.discounts:
            print(f"  {disc.discount_name} on {disc.applied_to_item_name}: -${disc.discount_amount:.2f}")
```

### Filter by transaction type

Retrieve only specific transaction types to focus your analysis:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Get all recurring membership transactions
    recurring_txns = client.transactions.list_by_type(
        "recurring",
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    print(f"Found {len(recurring_txns)} recurring transactions")

    # Get all gift card transactions
    gc_txns = client.transactions.list_by_type(
        "giftcard",
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    print(f"Found {len(gc_txns)} gift card transactions")
```

### Use the v2 endpoint for enriched data

The v2 endpoint adds `customer_id`, recurring flags, and transaction status to
each list item:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    transactions = client.transactions.list_v2(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    for txn in transactions:
        flags = []
        if txn.is_recurring_plan_sale:
            flags.append("recurring-sale")
        if txn.is_recurring_plan_redemption:
            flags.append("recurring-redemption")

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(
            f"#{txn.trans_number}: ${txn.total:.2f} - "
            f"Status: {txn.transaction_status}"
            f"{flag_str}"
        )
```

### Batch export with load_job

The `load_job()` method is designed for bulk data exports. It submits a batch
job to the API, automatically polls for completion, and paginates through all
results:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Export one day of transactions (max 24-hour range)
    results = client.transactions.load_job(
        startDate="2025-06-15",
        endDate="2025-06-16",
        site="JOLIET",
    )

    print(f"Exported {len(results)} transactions")

    for txn in results:
        print(
            f"#{txn.number} at {txn.location_code}: "
            f"${txn.total:.2f} ({txn.transaction_status})"
        )
```

You can customize the polling behavior:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    results = client.transactions.load_job(
        startDate="2025-06-15",
        endDate="2025-06-16",
        site="JOLIET",
        poll_interval=5.0,   # Check every 5 seconds
        timeout=600.0,       # Wait up to 10 minutes
    )
```

## Batch Job Workflow

The `load_job()` method is the most complex operation in the SDK. Under the
hood, it orchestrates a multi-step batch job workflow against two API endpoints.
This section explains how it works so you can understand the timing, error
handling, and pagination behavior.

### How It Works

Each call to `load_job()` follows a three-phase workflow: submit the job, poll
for completion, and return the results.

```text
  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
  │  Submit Job  │────>│  Poll Status  │────>│   Return    │
  │  POST        │     │  GET          │     │   Results   │
  │  /load-job   │     │  /get-job-data│     │             │
  └─────────────┘     └──────┬───────┘     └─────────────┘
                             │
                        ┌────▼────┐
                        │ Status? │
                        └────┬────┘
                    ┌────────┼────────┐
                    ▼        ▼        ▼
                 "pass"  "working"  "fail"
                   │        │        │
                   │     sleep &     │
                   │     retry ──┐   │
                   │        ^    │   │
                   │        └────┘   │
                   ▼                 ▼
               Return data     Raise APIError
```

1. **Submit** -- The client sends a `POST` request to `/transaction/load-job`
   with your query parameters. The API returns a `hash` identifier for the job.
2. **Poll** -- The client sends `GET` requests to `/transaction/get-job-data`
   with the job hash, sleeping `poll_interval` seconds between attempts.
3. **Return** -- When the status reaches `"pass"`, the response contains the
   transaction data. The client validates each record into a
   `TransactionJobItem` model and returns the full list.

!!! tip "Debug logging"
    Enable `DEBUG` logging on `sonnys_data_client` to see the full job
    lifecycle: job submission with parameters, hash returned, each poll
    attempt, pending/complete status transitions, and final record count.

### Job Status Lifecycle

Each polling response includes a `status` field with one of three values:

- **`"working"`** -- The job is still processing. The client sleeps for
  `poll_interval` seconds (default 2.0) and sends another poll request.
- **`"pass"`** -- The job completed successfully. Transaction data is available
  in the response body.
- **`"fail"`** -- The job failed on the server side. The client raises an
  `APIError` with the message `"Batch job failed"`.

### Multi-Page Jobs

Pagination for `load_job()` happens at the job submission level, not within a
single job response. Each `POST /transaction/load-job` with a different `offset`
value submits a separate batch job. The client handles this automatically:

1. The first job is submitted with `offset=1` (or your custom starting offset).
2. The response includes a `total` field indicating the total number of records.
3. The client calculates how many additional pages are needed based on `total`
   and the `limit` (default 100 records per page).
4. Each remaining page submits a new job and goes through its own submit, poll,
   and return cycle.

All results are collected and returned as a single flat list.

### Timeouts and Errors

Two error conditions can occur during the batch job workflow:

- **`APIError("Batch job failed")`** -- Raised when the API returns a job
  status of `"fail"`. This indicates a server-side error processing your
  request. Retry with the same parameters or narrow your date range.
- **`APITimeoutError`** -- Raised when a single job does not reach `"pass"` or
  `"fail"` within the `timeout` period (default 300 seconds / 5 minutes).
  Increase the `timeout` parameter if you expect slow processing.

!!! warning "Timeout applies per job page"
    The `timeout` parameter applies to **each individual job page**, not to the
    entire `load_job()` call. For example, a query returning 500 records with
    the default limit of 100 submits 5 separate jobs. Each job has its own
    300-second timeout, so the theoretical maximum wall time is
    5 x 300 = 1,500 seconds (25 minutes).

## Models

### `TransactionListItem`

Returned by `list()` and `list_by_type()`. Contains summary fields.

| Field          | Type    | Description                     |
|----------------|---------|---------------------------------|
| `trans_number` | `int`   | Transaction number              |
| `trans_id`     | `str`   | Unique transaction identifier   |
| `total`        | `float` | Transaction total amount        |
| `date`         | `str`   | Transaction date                |

### `TransactionV2ListItem`

Returned by `list_v2()`. Extends `TransactionListItem` with enriched fields.

| Field                        | Type           | Description                         |
|------------------------------|----------------|-------------------------------------|
| `trans_number`               | `int`          | Transaction number                  |
| `trans_id`                   | `str`          | Unique transaction identifier       |
| `total`                      | `float`        | Transaction total amount            |
| `date`                       | `str`          | Transaction date                    |
| `customer_id`                | `str \| None`  | Associated customer identifier      |
| `is_recurring_plan_sale`     | `bool`         | Whether this is a recurring sale    |
| `is_recurring_plan_redemption`| `bool`        | Whether this is a recurring redemption |
| `transaction_status`         | `str`          | Transaction status                  |

### `Transaction`

Returned by `get()`. Contains full transaction details with nested models.

| Field                    | Type                        | Description                          |
|--------------------------|-----------------------------|--------------------------------------|
| `id`                     | `str`                       | Unique transaction identifier        |
| `number`                 | `int`                       | Transaction number                   |
| `type`                   | `str`                       | Transaction type                     |
| `complete_date`          | `str`                       | Date and time of the transaction     |
| `location_code`          | `str`                       | Site location code                   |
| `sales_device_name`      | `str`                       | Name of the sales device / POS       |
| `total`                  | `float`                     | Transaction total amount             |
| `customer_name`          | `str \| None`               | Customer name                        |
| `customer_id`            | `str \| None`               | Customer identifier                  |
| `vehicle_license_plate`  | `str \| None`               | Vehicle license plate                |
| `employee_cashier`       | `str \| None`               | Cashier employee name                |
| `employee_greeter`       | `str \| None`               | Greeter employee name                |
| `is_recurring_payment`   | `bool`                      | Recurring payment flag               |
| `is_recurring_redemption`| `bool`                      | Recurring redemption flag            |
| `is_recurring_sale`      | `bool`                      | Recurring sale flag                  |
| `is_prepaid_redemption`  | `bool`                      | Prepaid redemption flag              |
| `is_prepaid_sale`        | `bool`                      | Prepaid sale flag                    |
| `tenders`                | `list[TransactionTender]`   | Payment tenders (see below)          |
| `items`                  | `list[TransactionItem]`     | Line items (see below)               |
| `discounts`              | `list[TransactionDiscount]` | Applied discounts (see below)        |

### `TransactionJobItem`

Returned by `load_job()`. Extends `Transaction` with v2 enrichment fields.

This model inherits all fields from `Transaction` (see above) plus:

| Field                         | Type           | Description                           |
|-------------------------------|----------------|---------------------------------------|
| `customer_id`                 | `str \| None`  | Associated customer identifier        |
| `is_recurring_plan_sale`      | `bool \| None` | Whether this is a recurring sale      |
| `is_recurring_plan_redemption`| `bool \| None` | Whether this is a recurring redemption|
| `transaction_status`          | `str \| None`  | Transaction status                    |

### `TransactionTender`

Nested inside `Transaction` and `TransactionJobItem`.

| Field                        | Type           | Description                    |
|------------------------------|----------------|--------------------------------|
| `tender`                     | `str`          | Tender type name               |
| `tender_sub_type`            | `str \| None`  | Tender sub-type                |
| `amount`                     | `float`        | Tender amount                  |
| `change`                     | `float`        | Change given                   |
| `total`                      | `float`        | Net tender total               |
| `reference_number`           | `str \| None`  | Payment reference number       |
| `credit_card_last_four`      | `str \| None`  | Last four digits of card       |
| `credit_card_expiration_date`| `str \| None`  | Card expiration date           |

### `TransactionItem`

Nested inside `Transaction` and `TransactionJobItem`.

| Field            | Type    | Description                    |
|------------------|---------|--------------------------------|
| `name`           | `str`   | Item name                      |
| `sku`            | `str \| None` | Item SKU                 |
| `department`     | `str`   | Department name                |
| `quantity`       | `int`   | Quantity sold                  |
| `gross`          | `float` | Gross amount                   |
| `net`            | `float` | Net amount                     |
| `discount`       | `float` | Discount amount                |
| `tax`            | `float` | Tax amount                     |
| `additional_fee` | `float` | Additional fees                |
| `is_voided`      | `bool`  | Whether the item was voided    |

### `TransactionDiscount`

Nested inside `Transaction` and `TransactionJobItem`.

| Field                  | Type           | Description                    |
|------------------------|----------------|--------------------------------|
| `discount_name`        | `str`          | Discount name                  |
| `discount_sku`         | `str \| None`  | Discount SKU                   |
| `applied_to_item_name` | `str`          | Item the discount was applied to|
| `discount_amount`      | `float`        | Amount discounted              |
| `discount_code`        | `str`          | Discount code                  |

## Advanced Patterns

### Multi-Day Exports

Since `load_job()` is limited to a 24-hour date range per call, use a loop to
export multiple days:

```python
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
            site="JOLIET",
        )
        all_results.extend(day_results)
        current = next_day

    print(f"Exported {len(all_results)} transactions over {(end - start).days} days")
```

!!! tip "Spacing requests for large exports"
    For very large exports, consider adding a small `time.sleep()` between days
    to stay well within the rate limit. The client handles 429 retries
    automatically, but spacing requests reduces retry churn.

### Error Handling

Transaction-specific error handling patterns:

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import (
    APIError,
    APITimeoutError,
    RateLimitError,
    ValidationError,
)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        results = client.transactions.load_job(
            startDate="2025-06-15",
            endDate="2025-06-16",
            site="JOLIET",
            timeout=600.0,
        )
    except APITimeoutError:
        print("Job timed out — try a shorter date range or increase timeout")
    except APIError as e:
        print(f"Job failed: {e}")
    except RateLimitError:
        print("Rate limit exceeded after max retries")
```

!!! note "`ValidationError`"
    `ValidationError` is raised when date format is invalid or parameters fail
    API validation. This is caught before the request is sent, so it does not
    count against the rate limit.

### Cross-Resource Lookups

Enrich transaction data by combining with other resources:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Get enriched transactions with customer_id
    transactions = client.transactions.list_v2(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    # Build customer lookup from customer_ids found in transactions
    customer_ids = {t.customer_id for t in transactions if t.customer_id}
    customers = {
        c.customer_id: c
        for c in client.customers.list()
        if c.customer_id in customer_ids
    }

    # Enrich transactions with customer names
    for txn in transactions:
        if txn.customer_id and txn.customer_id in customers:
            customer = customers[txn.customer_id]
            print(f"#{txn.trans_number}: ${txn.total:.2f} — {customer.first_name} {customer.last_name}")
```

!!! note "Auto-pagination"
    The `list()`, `list_by_type()`, and `list_v2()` methods automatically fetch
    all pages of results. The `load_job()` method handles pagination at the job
    submission level, submitting multiple jobs as needed.
