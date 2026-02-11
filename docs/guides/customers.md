# Customers

The **Customers** resource provides access to car wash customer records. Each
customer includes contact information, loyalty data, and an optional mailing
address. Use this resource to retrieve customer lists or fetch full details for
a single customer by ID.

## Methods

### `list(**params) -> list[CustomerListItem]`

Fetch all customers. Returns a list of `CustomerListItem` objects with summary
fields. The client automatically paginates through all pages of results.

```python
customers = client.customers.list()
```

You can pass optional query parameters to filter results:

```python
customers = client.customers.list(
    startDate="2025-01-01",
    endDate="2025-01-31",
)
```

### `get(customer_id) -> Customer`

Fetch full details for a single customer by their ID. Returns a `Customer`
object with all fields including address, email, loyalty number, and SMS
preferences.

```python
customer = client.customers.get("12345")
```

## Examples

### List all customers

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    customers = client.customers.list()

    for c in customers:
        print(f"{c.first_name} {c.last_name} (ID: {c.customer_id})")
```

### Filter customers by date range

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    recent = client.customers.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )
    print(f"Found {len(recent)} customers modified in June 2025")
```

### Get customer detail by ID

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    customer = client.customers.get("12345")

    print(f"Name:    {customer.first_name} {customer.last_name}")
    print(f"Email:   {customer.email}")
    print(f"Phone:   {customer.phone}")
    print(f"Loyalty: {customer.loyalty_number}")
    print(f"Active:  {customer.is_active}")
```

### Access nested address fields

The `Customer` detail model includes an `Address` object with full mailing
address fields:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    customer = client.customers.get("12345")

    addr = customer.address
    print(f"{addr.address1}")
    print(f"{addr.city}, {addr.state} {addr.postal_code}")
```

## Models

### `CustomerListItem`

Returned by `list()`. Contains summary fields for each customer.

| Field             | Type           | Description                    |
|-------------------|----------------|--------------------------------|
| `customer_id`     | `str`          | Unique customer identifier     |
| `first_name`      | `str`          | Customer first name            |
| `last_name`       | `str`          | Customer last name             |
| `phone_number`    | `str \| None`  | Phone number                   |
| `customer_number` | `str \| None`  | Customer account number        |
| `is_active`       | `bool`         | Whether the customer is active |
| `created_date`    | `str`          | Date the record was created    |
| `modified_date`   | `str \| None`  | Date the record was last modified |

### `Customer`

Returned by `get()`. Contains full customer details including address.

| Field                       | Type           | Description                          |
|-----------------------------|----------------|--------------------------------------|
| `id`                        | `str`          | Unique customer identifier           |
| `number`                    | `str`          | Customer account number              |
| `first_name`                | `str`          | Customer first name                  |
| `last_name`                 | `str`          | Customer last name                   |
| `company_name`              | `str \| None`  | Company name                         |
| `loyalty_number`            | `str \| None`  | Loyalty program number               |
| `address`                   | `Address`      | Nested address object (see below)    |
| `phone`                     | `str`          | Phone number                         |
| `email`                     | `str \| None`  | Email address                        |
| `birth_date`                | `str \| None`  | Date of birth                        |
| `is_active`                 | `bool`         | Whether the customer is active       |
| `allow_sms`                 | `bool`         | SMS opt-in status                    |
| `recurring_sms_signup_date` | `str \| None`  | Date of recurring SMS signup         |
| `loyalty_sms_signup_date`   | `str \| None`  | Date of loyalty SMS signup           |
| `modify_date`               | `str`          | Date the record was last modified    |

### `Address`

Nested inside the `Customer` model.

| Field         | Type           | Description        |
|---------------|----------------|--------------------|
| `address1`    | `str \| None`  | Street address     |
| `address2`    | `str \| None`  | Suite / unit       |
| `city`        | `str \| None`  | City               |
| `state`       | `str \| None`  | State              |
| `country`     | `str \| None`  | Country            |
| `postal_code` | `str \| None`  | ZIP / postal code  |

!!! note "Auto-pagination"
    The `list()` method automatically fetches all pages of results. You do not
    need to handle pagination manually -- the client will continue requesting
    pages until all records have been retrieved.

!!! tip "Full model reference"
    For the complete field definitions and type annotations, see the
    [Models](../api/models.md) page in the API Reference.
