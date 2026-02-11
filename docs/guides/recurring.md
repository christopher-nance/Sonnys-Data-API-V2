# Recurring Accounts

The **Recurring Accounts** resource provides access to recurring (membership)
car wash accounts. This is the richest standard resource in the client, offering
five methods for listing accounts, fetching full details, tracking status
changes, and reviewing modification history. Each account includes billing
information, plan details, associated tags, vehicles, and customer data.

## Methods

### `list(**params) -> list[RecurringListItem]`

Fetch all recurring accounts. Returns a list of `RecurringListItem` objects with
summary fields. The client automatically paginates through all pages of results.

```python
accounts = client.recurring.list()
```

You can pass optional query parameters to filter results:

```python
accounts = client.recurring.list(
    startDate="2025-01-01",
    endDate="2025-01-31",
)
```

### `get(account_id) -> Recurring`

Fetch full details for a single recurring account by its ID. Returns a
`Recurring` object with nested customer, tags, vehicles, billing history, and
status history.

```python
account = client.recurring.get("12345")
```

### `list_status_changes(**params) -> list[RecurringStatusChange]`

Fetch all recurring account status changes. Returns a list of
`RecurringStatusChange` objects tracking when accounts changed status (e.g.,
active to cancelled).

```python
changes = client.recurring.list_status_changes()
```

### `list_modifications(**params) -> list[RecurringModification]`

Fetch all recurring account modifications. Returns a list of
`RecurringModification` objects -- each includes the full account detail plus a
list of modification entries.

```python
modifications = client.recurring.list_modifications()
```

### `list_details(**params) -> list[Recurring]`

Fetch all recurring accounts with full detail. Returns full `Recurring` objects
(the same model as `get()`) for every account, rather than the summary
`RecurringListItem` objects returned by `list()`.

```python
details = client.recurring.list_details()
```

!!! warning "Heavier API call"
    `list_details()` returns full `Recurring` objects for every account. This
    results in significantly more data per request than `list()`. Use `list()`
    when you only need summary fields, and reserve `list_details()` for when
    you need the complete account data in bulk.

## Examples

### List recurring accounts

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    accounts = client.recurring.list()

    for acct in accounts:
        print(
            f"Account {acct.id}: {acct.status_name} "
            f"(status={acct.status}, site={acct.billing_site_code})"
        )
```

### Get account detail

The detail endpoint returns billing info, plan details, tags, vehicles,
customer data, and full status and billing history:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    acct = client.recurring.get("12345")

    # Plan and billing info
    print(f"Plan: {acct.plan_name}")
    print(f"Billing amount: ${acct.billing_amount:.2f}")
    print(f"Next bill date: {acct.next_bill_date}")
    print(f"On trial: {acct.is_on_trial}")
    print(f"Suspended: {acct.is_suspended}")

    # Customer
    print(f"Customer: {acct.customer.first_name} {acct.customer.last_name}")

    # Tags and vehicles
    for tag in acct.tags:
        print(f"Tag #{tag.number} - {'active' if tag.enabled else 'disabled'}")
    for vehicle in acct.vehicles:
        print(f"Vehicle {vehicle.id}: {vehicle.plate or 'No plate'}")

    # Status history
    for status in acct.recurring_statuses:
        print(f"Status: {status.status} on {status.date}")

    # Billing history
    for billing in acct.recurring_billings:
        print(f"Billed ${billing.amount_charged:.2f} on {billing.date}")
```

### Track status changes

The `list_status_changes()` method returns a flat list of every status
transition across all accounts:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    changes = client.recurring.list_status_changes(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    for change in changes:
        print(
            f"Account {change.recurring_id}: "
            f"{change.old_status} -> {change.new_status} "
            f"on {change.status_date} "
            f"(by {change.employee_name} at {change.site_code})"
        )
```

### Review modifications

The `list_modifications()` method returns full account objects extended with a
`modifications` list:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    modified = client.recurring.list_modifications(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    for acct in modified:
        print(f"Account {acct.id} ({acct.plan_name}):")
        for mod in acct.modifications:
            comment = mod.comment or "No comment"
            print(f"  {mod.date}: {mod.name} - {comment}")
```

### Compare list vs list_details

Use `list()` for lightweight summaries and `list_details()` when you need the
full account data:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Lightweight: returns RecurringListItem objects
    summaries = client.recurring.list()
    print(f"Found {len(summaries)} accounts (summary)")

    # Full detail: returns Recurring objects (same as get())
    details = client.recurring.list_details()
    print(f"Found {len(details)} accounts (full detail)")

    # Full detail includes nested data not available in summaries
    for acct in details:
        print(
            f"Account {acct.id}: {acct.plan_name}, "
            f"{len(acct.tags)} tags, {len(acct.vehicles)} vehicles"
        )
```

## Models

### `RecurringListItem`

Returned by `list()`. Contains summary fields for each recurring account.

| Field               | Type           | Description                          |
|---------------------|----------------|--------------------------------------|
| `id`                | `str`          | Unique account identifier            |
| `name`              | `str \| None`  | Account name                         |
| `balance`           | `float \| None`| Current account balance              |
| `sign_up_date`      | `str`          | Date the account was created         |
| `cancel_date`       | `str \| None`  | Date the account was cancelled       |
| `billing_site_id`   | `int`          | ID of the billing site               |
| `customer_id`       | `str \| None`  | Associated customer identifier       |
| `status`            | `int`          | Numeric status code                  |
| `status_name`       | `str`          | Human-readable status name           |
| `billing_site_code` | `str`          | Site code of the billing site        |

### `Recurring`

Returned by `get()` and `list_details()`. Contains full account details with
nested models.

| Field                           | Type                      | Description                         |
|---------------------------------|---------------------------|-------------------------------------|
| `id`                            | `str`                     | Unique account identifier           |
| `is_on_trial`                   | `bool`                    | Whether the account is on trial     |
| `trial_amount`                  | `float`                   | Trial billing amount                |
| `billing_site_code`             | `str`                     | Site code of the billing site       |
| `creation_site_code`            | `str`                     | Site code where account was created |
| `next_bill_date`                | `str`                     | Next scheduled billing date         |
| `last_bill_date`                | `str \| None`             | Most recent billing date            |
| `billing_amount`                | `float \| None`           | Current billing amount              |
| `is_suspended`                  | `bool`                    | Whether the account is suspended    |
| `suspended_until`               | `str \| None`             | Suspension end date                 |
| `current_recurring_status_name` | `str`                     | Current status name                 |
| `plan_name`                     | `str`                     | Name of the wash plan               |
| `additional_tag_price`          | `float \| None`           | Price for additional tags           |
| `customer`                      | `WashbookCustomer`        | Nested customer object              |
| `tags`                          | `list[WashbookTag]`       | List of RFID tags                   |
| `vehicles`                      | `list[WashbookVehicle]`   | List of vehicles                    |
| `recurring_statuses`            | `list[RecurringStatus]`   | Status history (see below)          |
| `recurring_billings`            | `list[RecurringBilling]`  | Billing history (see below)         |

### `RecurringStatus`

Nested inside the `Recurring` model. Represents a single status history entry.

| Field    | Type   | Description          |
|----------|--------|----------------------|
| `status` | `str`  | Status name          |
| `date`   | `str`  | Date of the status   |

### `RecurringBilling`

Nested inside the `Recurring` model. Represents a single billing history entry.

| Field                        | Type           | Description                    |
|------------------------------|----------------|--------------------------------|
| `amount_charged`             | `float`        | Amount billed                  |
| `date`                       | `str`          | Billing date                   |
| `last_four_cc`               | `str`          | Last four digits of credit card|
| `credit_card_expiration_date`| `str \| None`  | Card expiration date           |

### `RecurringStatusChange`

Returned by `list_status_changes()`. Represents a single status transition.

| Field                  | Type   | Description                         |
|------------------------|--------|-------------------------------------|
| `washbook_account_id`  | `str`  | Associated washbook account ID      |
| `recurring_id`         | `str`  | Recurring account identifier        |
| `old_status`           | `str`  | Previous status                     |
| `new_status`           | `str`  | New status                          |
| `status_date`          | `str`  | Date of the status change           |
| `employee_name`        | `str`  | Employee who made the change        |
| `site_code`            | `str`  | Site where the change occurred      |

### `RecurringModification`

Returned by `list_modifications()`. Extends the `Recurring` model with a
modifications list.

This model inherits all fields from `Recurring` (see above) plus:

| Field           | Type                             | Description              |
|-----------------|----------------------------------|--------------------------|
| `modifications` | `list[RecurringModificationEntry]`| List of modifications    |

### `RecurringModificationEntry`

Nested inside `RecurringModification`.

| Field     | Type           | Description              |
|-----------|----------------|--------------------------|
| `name`    | `str`          | Modification name        |
| `date`    | `str`          | Date of the modification |
| `comment` | `str \| None`  | Optional comment         |

!!! note "Shared nested types"
    The `Recurring` model reuses `WashbookCustomer`, `WashbookTag`, and
    `WashbookVehicle` from the [Washbooks](washbooks.md) resource. See that
    guide for field-level documentation of those nested types.

!!! note "Auto-pagination"
    All list methods (`list()`, `list_status_changes()`, `list_modifications()`,
    and `list_details()`) automatically fetch all pages of results. You do not
    need to handle pagination manually.

!!! tip "See also"
    For patterns combining recurring accounts with transaction data, see the
    [Transactions](transactions.md#cross-resource-lookups) guide.
