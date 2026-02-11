# Resources

Resources are the primary interface for interacting with the Sonny's Data API.
Each resource is accessed as a property on the [`SonnysClient`](client.md) and
exposes methods like `list()`, `get()`, and resource-specific operations.

```python
with SonnysClient(api_id, api_key) as client:
    customers = client.customers.list()
    customer  = client.customers.get("12345")
```

## Base Classes

::: sonnys_data_client._resources.BaseResource
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client._resources.ListableResource
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client._resources.GettableResource
    options:
      show_source: false
      heading_level: 3

---

## Concrete Resources

::: sonnys_data_client.resources.Customers
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.Items
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.Employees
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.Sites
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.Giftcards
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.Washbooks
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.RecurringAccounts
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.Transactions
    options:
      show_source: false
      heading_level: 3

::: sonnys_data_client.resources.StatsResource
    options:
      show_source: false
      heading_level: 3
