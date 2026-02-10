# sonnys-data-client

> A typed Python SDK for the Sonny's Carwash Controls Data API.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green)
![License: MIT](https://img.shields.io/badge/license-MIT-yellow)
![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-brightgreen)

`sonnys-data-client` wraps the Sonny's Carwash Controls REST API with a
resource-based interface (`client.transactions.list()`,
`client.customers.get(id)`). Every response is returned as a validated Pydantic
v2 model, list calls auto-paginate transparently, and a built-in rate limiter
with exponential-backoff retry keeps your application within the API's
20-request/15-second window.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Client Configuration](#client-configuration)
- [Resources](#resources)
  - [Batch Jobs](#batch-jobs)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Multi-Site Usage](#multi-site-usage)
- [Requirements](#requirements)

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

## Client Configuration

### Constructor

```python
SonnysClient(
    api_id: str,
    api_key: str,
    site_code: str | None = None,
    *,
    max_retries: int = 3,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_id` | `str` | *required* | Sonny's API ID credential |
| `api_key` | `str` | *required* | Sonny's API key credential |
| `site_code` | `str \| None` | `None` | Optional site code to scope all requests to a single site |
| `max_retries` | `int` | `3` | Maximum retry attempts for 429 rate-limit responses (uses exponential backoff) |

### Context Manager

Use the `with` statement to ensure the underlying HTTP session is closed
automatically when you are done:

```python
with SonnysClient(api_id="id", api_key="key") as client:
    data = client.customers.list()
```

If you prefer manual lifecycle management, call `.close()` explicitly:

```python
client = SonnysClient(api_id="id", api_key="key")
try:
    data = client.customers.list()
finally:
    client.close()
```

### Authentication

Credentials are sent as HTTP headers on every request:

- `X-Sonnys-API-ID` -- from `api_id`
- `X-Sonnys-API-Key` -- from `api_key`
- `X-Sonnys-Site-Code` -- from `site_code` (omitted when `None`)

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
