# Washbooks

The **Washbooks** resource provides access to prepaid wash book accounts. Each
account tracks balances, sign-up and cancellation dates, and billing site
information. The detail endpoint expands each account with customer contact
info, RFID tags, associated vehicles, and recurring billing details.

## Methods

### `list(**params) -> list[WashbookListItem]`

Fetch all wash book accounts. Returns a list of `WashbookListItem` objects with
summary fields. The client automatically paginates through all pages of results.

```python
washbooks = client.washbooks.list()
```

You can pass optional query parameters to filter results:

```python
washbooks = client.washbooks.list(
    startDate="2025-01-01",
    endDate="2025-01-31",
)
```

### `get(account_id) -> Washbook`

Fetch full details for a single wash book account by its ID. Returns a
`Washbook` object with nested customer, tag, vehicle, and recurring billing
information.

```python
washbook = client.washbooks.get("12345")
```

## Examples

### List all wash book accounts

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    washbooks = client.washbooks.list()

    for wb in washbooks:
        print(f"{wb.name} (ID: {wb.id}) - Status: {wb.status}")
```

### Filter by date and check balances

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    recent = client.washbooks.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    for wb in recent:
        print(f"Account {wb.id}: balance={wb.balance}, site={wb.billing_site_id}")
```

### Get wash book detail with customer info

The detail endpoint returns rich nested data including the customer, tags,
vehicles, and recurring billing information:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    wb = client.washbooks.get("12345")

    # Customer information
    print(f"Customer: {wb.customer.first_name} {wb.customer.last_name}")
    print(f"Customer ID: {wb.customer.id}")

    # Account status and balance
    print(f"Status: {wb.status}")
    print(f"Balance: {wb.balance}")
```

### Iterate tags and vehicles

Each wash book detail includes lists of RFID tags and associated vehicles:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    wb = client.washbooks.get("12345")

    # RFID tags
    for tag in wb.tags:
        status = "active" if tag.enabled else "disabled"
        print(f"Tag #{tag.number} (ID: {tag.id}) - {status}")

    # Vehicles
    for vehicle in wb.vehicles:
        plate = vehicle.plate or "No plate"
        print(f"Vehicle {vehicle.id}: {plate}")
```

### Access recurring billing info

The `recurring_info` field provides current billing details and trial status:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    wb = client.washbooks.get("12345")

    info = wb.recurring_info
    print(f"Billing amount: ${info.current_billable_amount:.2f}")
    print(f"Next bill date: {info.next_bill_date}")
    print(f"Last bill date: {info.last_bill_date}")
    print(f"On trial: {info.is_on_trial}")
    if info.is_on_trial:
        print(f"Remaining trial periods: {info.remaining_trial_periods}")
```

## Models

### `WashbookListItem`

Returned by `list()`. Contains summary fields for each wash book account.

| Field            | Type           | Description                           |
|------------------|----------------|---------------------------------------|
| `id`             | `str`          | Unique account identifier             |
| `name`           | `str \| None`  | Account name                          |
| `balance`        | `str`          | Current account balance               |
| `sign_up_date`   | `str`          | Date the account was created          |
| `cancel_date`    | `str \| None`  | Date the account was cancelled        |
| `billing_site_id`| `int`          | ID of the billing site                |
| `customer_id`    | `str \| None`  | Associated customer identifier        |
| `status`         | `str`          | Current account status                |

### `Washbook`

Returned by `get()`. Contains full account details with nested models.

| Field            | Type                     | Description                        |
|------------------|--------------------------|------------------------------------|
| `id`             | `str`                    | Unique account identifier          |
| `name`           | `str`                    | Account name                       |
| `balance`        | `str \| None`            | Current account balance            |
| `customer`       | `WashbookCustomer`       | Nested customer object (see below) |
| `status`         | `str`                    | Current account status             |
| `recurring_info` | `WashbookRecurringInfo`  | Billing and trial info (see below) |
| `tags`           | `list[WashbookTag]`      | List of RFID tags (see below)      |
| `vehicles`       | `list[WashbookVehicle]`  | List of vehicles (see below)       |

### `WashbookCustomer`

Nested inside the `Washbook` model.

| Field        | Type           | Description              |
|--------------|----------------|--------------------------|
| `id`         | `str \| None`  | Customer identifier      |
| `number`     | `str \| None`  | Customer account number  |
| `first_name` | `str \| None`  | Customer first name      |
| `last_name`  | `str \| None`  | Customer last name       |

### `WashbookRecurringInfo`

Nested inside the `Washbook` model.

| Field                      | Type           | Description                     |
|----------------------------|----------------|---------------------------------|
| `current_billable_amount`  | `float`        | Current billing amount          |
| `next_bill_date`           | `str \| None`  | Next scheduled billing date     |
| `last_bill_date`           | `str \| None`  | Most recent billing date        |
| `is_on_trial`              | `bool`         | Whether the account is on trial |
| `remaining_trial_periods`  | `int`          | Number of trial periods left    |

### `WashbookTag`

Nested inside the `Washbook` model.

| Field     | Type   | Description               |
|-----------|--------|---------------------------|
| `id`      | `str`  | Unique tag identifier     |
| `number`  | `str`  | Tag number                |
| `enabled` | `bool` | Whether the tag is active |

### `WashbookVehicle`

Nested inside the `Washbook` model.

| Field   | Type           | Description              |
|---------|----------------|--------------------------|
| `id`    | `str`          | Unique vehicle identifier|
| `plate` | `str \| None`  | License plate number     |

!!! note "Nested model relationships"
    The `Washbook` detail model contains four nested types:
    `WashbookCustomer`, `WashbookRecurringInfo`, `WashbookTag`, and
    `WashbookVehicle`. These same nested types are also used by the
    [Recurring Accounts](recurring.md) resource.

!!! note "Auto-pagination"
    The `list()` method automatically fetches all pages of results. You do not
    need to handle pagination manually -- the client will continue requesting
    pages until all records have been retrieved.

!!! tip "Full model reference"
    For the complete field definitions and type annotations, see the
    [Models](../api/models.md) page in the API Reference.
