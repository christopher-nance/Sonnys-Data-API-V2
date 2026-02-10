# sonnys-data-client

Python client for the Sonny's Carwash Controls Data API.

## Installation

```bash
pip install git+https://github.com/WashU-CarWash/sonnys-data-client.git
```

## Quick Start

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    transactions = client.transactions.list(startDate="2024-01-01", endDate="2024-01-31")
    for txn in transactions:
        print(txn.transaction_id, txn.total)
```

All resources auto-paginate by default -- calling `.list()` returns every record
across all pages.

## Resources

| Resource | Methods |
|---|---|
| `client.customers` | `list(**params)`, `get(id)` |
| `client.items` | `list(**params)` |
| `client.employees` | `list(**params)`, `get(id)`, `get_clock_entries(employee_id, *, start_date, end_date)` |
| `client.sites` | `list(**params)` |
| `client.giftcards` | `list(**params)` |
| `client.washbooks` | `list(**params)`, `get(id)` |
| `client.recurring` | `list(**params)`, `get(id)`, `list_status_changes(**params)`, `list_modifications(**params)`, `list_details(**params)` |
| `client.transactions` | `list(**params)`, `get(id)`, `list_by_type(item_type, **params)`, `list_v2(**params)`, `load_job(*, poll_interval, timeout, **params)` |

Common query parameters passed via `**params` include `startDate`, `endDate`,
`site`, `region`, `limit`, and `offset`. Check the Sonny's API documentation
for endpoint-specific parameters.

### Batch Jobs

The `load_job` method submits a batch job and polls until results are ready:

```python
results = client.transactions.load_job(
    startDate="2024-01-01",
    endDate="2024-01-01",
    poll_interval=2.0,
    timeout=300.0,
)
```

The API caches job data for 20 minutes and limits the date range to 24 hours.

## Error Handling

All exceptions inherit from `SonnysError`:

```python
from sonnys_data_client import SonnysClient, SonnysError, AuthError, NotFoundError

with SonnysClient(api_id="id", api_key="key") as client:
    try:
        customer = client.customers.get("12345")
    except AuthError as e:
        print("Bad credentials:", e.message)
    except NotFoundError as e:
        print("Customer not found:", e.message)
    except SonnysError as e:
        print("API error:", e)
```

Exception hierarchy:

- `SonnysError` -- base for all errors
  - `APIError` -- base for API-specific errors
    - `APIConnectionError` -- connection failure
      - `APITimeoutError` -- request timeout
    - `APIStatusError` -- HTTP error response (has `status_code`, `body`, `error_type`)
      - `AuthError` -- 403 Forbidden
      - `RateLimitError` -- 429 Too Many Requests
      - `ValidationError` -- 400 / 422 bad request
      - `NotFoundError` -- 404 Not Found
      - `ServerError` -- 500+ server errors

Rate limiting is handled automatically -- the client retries 429 responses with
exponential backoff (up to `max_retries`, default 3). A built-in rate limiter
also throttles outgoing requests to stay under the API rate limit.

## Logging

The client uses Python standard logging under the `sonnys_data_client` logger.
Enable debug output to see HTTP requests, responses, and timing:

```python
import logging

logging.getLogger("sonnys_data_client").setLevel(logging.DEBUG)
logging.basicConfig()
```

Log levels:

- **DEBUG** -- request method/path/params, response status/elapsed time, rate limiter waits
- **WARNING** -- 429 rate limit retries

## Multi-Site Usage

Instantiate separate clients for each set of credentials:

```python
from sonnys_data_client import SonnysClient

washu = SonnysClient(api_id="washu-id", api_key="washu-key")
icon = SonnysClient(api_id="icon-id", api_key="icon-key")

washu_sites = washu.sites.list()
icon_sites = icon.sites.list()

washu.close()
icon.close()
```

Use `site_code` to scope a client to a single site:

```python
client = SonnysClient(api_id="id", api_key="key", site_code="SITE01")
```

## Requirements

- Python 3.10+
- [requests](https://docs.python-requests.org/) >= 2.28
- [pydantic](https://docs.pydantic.dev/) >= 2.10
