# Items

The **Items** resource provides access to the wash items and products catalog.
Each item represents a product or service offered at a car wash site, including
its SKU, pricing, and department classification. This is a list-only resource
-- there is no `get()` method for individual item detail.

## Methods

### `list(**params) -> list[Item]`

Fetch all items. Returns a list of `Item` objects representing the full product
catalog. The client automatically paginates through all pages of results.

```python
items = client.items.list()
```

## Examples

### List all items

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    items = client.items.list()

    for item in items:
        print(f"{item.sku}: {item.name} - ${item.price_at_site}")
```

### View item details with department info

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    items = client.items.list()

    for item in items:
        print(f"SKU:        {item.sku}")
        print(f"Name:       {item.name}")
        print(f"Department: {item.department_name}")
        print(f"Price:      {item.price_at_site}")
        print(f"Site:       {item.site_location}")
        print()
```

### Group items by department

```python
from collections import defaultdict

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    items = client.items.list()

    by_department = defaultdict(list)
    for item in items:
        by_department[item.department_name].append(item)

    for dept, dept_items in by_department.items():
        print(f"\n{dept} ({len(dept_items)} items):")
        for item in dept_items:
            print(f"  {item.sku}: {item.name} - ${item.price_at_site}")
```

### Filter items by site location

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    items = client.items.list()

    site_items = [i for i in items if i.site_location == "MAIN"]
    print(f"Found {len(site_items)} items at MAIN site")
```

## Models

### `Item`

Returned by `list()`. Contains product catalog information.

| Field                | Type           | Description                              |
|----------------------|----------------|------------------------------------------|
| `sku`                | `str`          | Stock keeping unit identifier            |
| `name`              | `str`          | Product or service name                  |
| `department_name`    | `str`          | Department classification                |
| `price_at_site`      | `str`          | Price at the associated site             |
| `cost_per_item`      | `str \| None`  | Cost per item (if available)             |
| `is_prompt_for_price`| `bool`         | Whether the price is entered at the POS  |
| `site_location`      | `str`          | Site location code where the item is sold|

!!! note "Auto-pagination"
    The `list()` method automatically fetches all pages of results. You do not
    need to handle pagination manually -- the client will continue requesting
    pages until all records have been retrieved.

!!! info "List-only resource"
    Items is a list-only resource. There is no `get()` method to retrieve a
    single item by ID. Use `list()` and filter the results in Python if you
    need a specific item.

!!! tip "Full model reference"
    For the complete field definitions and type annotations, see the
    [Models](../api/models.md) page in the API Reference.
