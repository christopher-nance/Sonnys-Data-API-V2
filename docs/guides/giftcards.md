# Giftcards

The **Giftcards** resource provides access to gift card liability records. Each
record tracks a gift card's original value, amount used, and the site where it
was sold. Use this resource to retrieve gift card balances and monitor usage
across your locations.

## Methods

### `list(**params) -> list[GiftcardListItem]`

Fetch all gift card records. Returns a list of `GiftcardListItem` objects. The
client automatically paginates through all pages of results.

```python
giftcards = client.giftcards.list()
```

You can pass optional query parameters to filter results:

```python
giftcards = client.giftcards.list(
    startDate="2025-01-01",
    endDate="2025-01-31",
)
```

!!! info "List-only resource"
    The Giftcards resource only supports the `list()` method. There is no
    `get()` method for retrieving individual gift card details.

## Examples

### List all gift cards

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    giftcards = client.giftcards.list()

    for gc in giftcards:
        print(f"Card #{gc.number} (ID: {gc.giftcard_id}) - Site: {gc.site_code}")
```

### Check gift card balances

Each gift card record includes the original `value` and `amount_used`. Calculate
the remaining balance by subtracting `amount_used` from `value`:

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    giftcards = client.giftcards.list()

    for gc in giftcards:
        remaining = gc.value - gc.amount_used
        print(
            f"Card #{gc.number}: "
            f"Value=${gc.value:.2f}, "
            f"Used=${gc.amount_used:.2f}, "
            f"Remaining=${remaining:.2f}"
        )
```

### Summarize gift card liability by site

```python
from collections import defaultdict

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    giftcards = client.giftcards.list()

    liability_by_site: dict[str, float] = defaultdict(float)
    for gc in giftcards:
        remaining = gc.value - gc.amount_used
        liability_by_site[gc.site_code] += remaining

    for site, total in sorted(liability_by_site.items()):
        print(f"Site {site}: ${total:.2f} outstanding")
```

## Models

### `GiftcardListItem`

Returned by `list()`. Contains the full gift card record.

| Field           | Type           | Description                          |
|-----------------|----------------|--------------------------------------|
| `giftcard_id`   | `str`          | Unique gift card identifier          |
| `number`        | `str`          | Gift card number                     |
| `value`         | `float`        | Original gift card value             |
| `amount_used`   | `float`        | Total amount redeemed                |
| `site_code`     | `str`          | Site where the gift card was sold    |
| `complete_date` | `str \| None`  | Date the gift card was fully used    |

## Advanced Patterns

### Liability Tracking with Transactions

Combine gift card records with gift card transaction data to track redemptions
and calculate outstanding liability:

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    giftcards = client.giftcards.list()
    gc_txns = client.transactions.list_by_type(
        "giftcard",
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

    # Outstanding liability
    total_liability = sum(gc.value - gc.amount_used for gc in giftcards)
    print(f"Total outstanding liability: ${total_liability:.2f}")
    print(f"Gift card transactions this month: {len(gc_txns)}")
    print(f"Active cards: {sum(1 for gc in giftcards if gc.value > gc.amount_used)}")
```

!!! note "Auto-pagination"
    The `list()` method automatically fetches all pages of results. You do not
    need to handle pagination manually -- the client will continue requesting
    pages until all records have been retrieved.
