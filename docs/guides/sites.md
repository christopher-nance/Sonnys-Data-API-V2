# Sites

The **Sites** resource provides access to the car wash site locations associated
with your API credentials. Each site represents a physical car wash location
with its identifying code, name, and timezone. This is a list-only resource
-- there is no `get()` method for individual site detail.

## Methods

### `list(**params) -> list[Site]`

Fetch all sites. Returns a list of `Site` objects representing every car wash
location associated with the API credentials.

```python
sites = client.sites.list()
```

!!! warning "Not paginated"
    Unlike other resources, the Sites endpoint is **not paginated**. It returns
    all sites in a single API call. The `list()` method makes exactly one
    request regardless of how many sites exist.

## Examples

### List all sites

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    sites = client.sites.list()

    for site in sites:
        print(f"{site.code}: {site.name} ({site.timezone})")
```

### Access site fields

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    sites = client.sites.list()

    for site in sites:
        print(f"Site ID:  {site.site_id}")
        print(f"Code:     {site.code}")
        print(f"Name:     {site.name}")
        print(f"Timezone: {site.timezone}")
        print()
```

### Build a site code lookup

Site codes are used as filter parameters in other resources. Building a lookup
dictionary can be helpful when working across multiple resources:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    sites = client.sites.list()

    # Map site codes to site names
    site_names = {site.code: site.name for site in sites}

    # Use in combination with other resources
    transactions = client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-01",
    )

    for txn in transactions:
        name = site_names.get(txn.site_code, "Unknown")
        print(f"{txn.transaction_id} at {name}")
```

## Models

### `Site`

Returned by `list()`. Contains site location information.

| Field      | Type           | Description                        |
|------------|----------------|------------------------------------|
| `site_id`  | `int`          | Unique site identifier             |
| `code`     | `str \| None`  | Site code (used in other API calls)|
| `name`     | `str`          | Display name of the site           |
| `timezone` | `str \| None`  | Timezone of the site location      |

!!! tip "Site codes in other resources"
    Site codes appear throughout other resources (e.g., transactions, clock
    entries) as a foreign key. Use `sites.list()` to retrieve the full site
    names and details for those codes.

!!! tip "Full model reference"
    For the complete field definitions and type annotations, see the
    [Models](../api/models.md) page in the API Reference.
