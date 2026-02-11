# Error Handling

The SDK raises typed exceptions for every failure mode so your code can react
precisely to each problem. Every exception inherits from `SonnysError`, letting
you catch broadly or narrow down to specific error types depending on your needs.

## Exception Hierarchy

All SDK exceptions follow this inheritance tree. Catching a parent class also
catches all of its children.

```
SonnysError                     # Base for all SDK errors
  APIError                      # Base for API-related errors
    APIConnectionError          # Network failures (DNS, refused, etc.)
      APITimeoutError           # Request timed out before a response
    APIStatusError              # HTTP error responses (4xx / 5xx)
      AuthError                 # 403 -- credential or authorization problem
      RateLimitError            # 429 -- rate limit exceeded
      ValidationError           # 400 / 422 -- bad request parameters
      NotFoundError             # 404 -- resource not found
      ServerError               # 5xx -- server-side failure
```

## Catching Errors

### Catch-all

The simplest approach catches `SonnysError` to handle any SDK failure in one
place:

```python
from sonnys_data_client import SonnysClient, SonnysError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        transactions = client.transactions.list(
            startDate="2025-06-01",
            endDate="2025-06-30",
        )
    except SonnysError as e:
        print(f"SDK error: {e}")
```

### Catch by category

Separate network problems from HTTP errors to apply different recovery
strategies:

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import (
    APIConnectionError,
    APIStatusError,
    SonnysError,
)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        customers = client.customers.list()
    except APIConnectionError:
        print("Network problem -- check your connection")
    except APIStatusError as e:
        print(f"HTTP {e.status_code}: {e.message}")
    except SonnysError as e:
        print(f"Other SDK error: {e}")
```

### Catch specific exceptions

For fine-grained control, catch each exception type individually:

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    SonnysError,
)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        customer = client.customers.get("12345")
    except AuthError:
        print("Invalid credentials or unauthorized site")
    except NotFoundError:
        print("Customer not found")
    except RateLimitError:
        print("Rate limit exceeded after retries")
    except ValidationError as e:
        print(f"Bad request: {e.message}")
    except ServerError:
        print("Server error -- try again later")
    except SonnysError as e:
        print(f"Unexpected SDK error: {e}")
```

!!! tip
    Order specific exceptions before general ones -- Python matches the first
    `except` clause. Place `AuthError` before `APIStatusError`, and
    `APIStatusError` before `SonnysError`.

## Error Attributes

All `APIStatusError` subclasses (`AuthError`, `RateLimitError`,
`ValidationError`, `NotFoundError`, `ServerError`) expose these attributes:

| Attribute     | Type           | Description                                                        |
|---------------|----------------|--------------------------------------------------------------------|
| `message`     | `str`          | Human-readable error description from the API                      |
| `status_code` | `int`          | HTTP status code (e.g., 403, 404, 429)                             |
| `body`        | `dict \| None` | Full parsed JSON response body from the API                        |
| `error_type`  | `str \| None`  | Sonny's API error type string (e.g., `"BadClientCredentialsError"`) |

Access these attributes in your `except` block to log details or branch on
the specific error type:

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APIStatusError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        transactions = client.transactions.list(
            startDate="2025-06-01",
            endDate="2025-06-30",
        )
    except APIStatusError as e:
        print(f"Status:     {e.status_code}")
        print(f"Message:    {e.message}")
        print(f"Error type: {e.error_type}")
        print(f"Body:       {e.body}")
```

!!! info "API error_type values"
    The `error_type` attribute contains the raw error type string returned by
    the Sonny's API. The SDK maps these to exception classes automatically:

    | API `error_type`                      | HTTP Status | SDK Exception     |
    |---------------------------------------|-------------|-------------------|
    | `MissingClientCredentialsError`        | 403         | `AuthError`       |
    | `BadClientCredentialsError`            | 403         | `AuthError`       |
    | `MismatchCredentialsError`             | 403         | `AuthError`       |
    | `NotAuthorizedError`                   | 403         | `AuthError`       |
    | `BadSiteCredentialsError`              | 403         | `AuthError`       |
    | `NotAuthorizedSiteCredentialsError`    | 403         | `AuthError`       |
    | `NotAuthorizedSiteArgsError`           | 403         | `AuthError`       |
    | `RequestRateExceedError`               | 429         | `RateLimitError`  |
    | `PayloadValidationError`               | 422         | `ValidationError` |
    | `InvalidPayloadRequestTimestampError`  | 400         | `ValidationError` |
    | `EntityNotFoundError`                  | 404         | `NotFoundError`   |
    | `UnexpectedFailure`                    | 400         | `APIError`        |
    | `ServerUnexpectedFailure`              | 500         | `ServerError`     |

## Per-Exception-Type Guidance

### AuthError

**When it is raised:** The API returns HTTP 403 for any credential or
authorization problem.

**Common causes:**

- Wrong `api_id` or `api_key` values (e.g., copied from the wrong environment or database)
- `site_code` not authorized for the given API ID -- each API ID is provisioned for specific sites, and using a site code from a different organization triggers `NotAuthorizedSiteCredentialsError`
- Missing credentials -- forgetting to pass `api_id` or `api_key` to the constructor
- API ID/key pair mismatch -- using the API ID from one database (e.g., WashU) with the API key from another (e.g., Icon)
- Passing `site` as a query parameter instead of using the `site_code` constructor argument

**Recommended handling:** Do not retry -- fix your credentials or site code
configuration. Check that your `api_id`, `api_key`, and `site_code` match what
was provisioned by Sonny's. Use `error_type` to pinpoint the exact problem.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import AuthError

with SonnysClient(
    api_id="your-api-id",
    api_key="your-api-key",
    site_code="SITE01",
) as client:
    try:
        sites = client.sites.list()
    except AuthError as e:
        print(f"Auth failed: {e.message}")
        print(f"Error type: {e.error_type}")

        # Branch on the specific auth failure
        if e.error_type == "BadClientCredentialsError":
            print("Check your api_id and api_key values")
        elif e.error_type == "NotAuthorizedSiteCredentialsError":
            print("This site_code is not authorized for your API ID")
        elif e.error_type == "MissingClientCredentialsError":
            print("Credentials were not provided")
        elif e.error_type == "MismatchCredentialsError":
            print("API ID and key do not belong to the same account")
```

!!! warning
    If you operate multiple databases (e.g., WashU and Icon) with separate
    credentials, double-check that you are not mixing API IDs and keys across
    client instances. A `MismatchCredentialsError` means the ID and key belong
    to different accounts.

### RateLimitError

**When it is raised:** The API returns HTTP 429 and all built-in retries have
been exhausted (default: 3 attempts with exponential backoff).

**Common causes:**

- Running an analytics script while a scheduled cron job is also pulling data against the same API ID
- Bulk-exporting transactions for multiple sites in a tight loop without pausing between sites
- Multiple `SonnysClient` instances sharing the same `api_id` -- each instance has its own rate limiter, but the API enforces a single 20 req/15s limit per API ID
- Burst traffic from a loop that calls `client.transactions.get()` for hundreds of individual transaction IDs

**Recommended handling:** The SDK already retries 429 responses with exponential
backoff (see [Built-in Retry Behavior](#built-in-retry-behavior)). If this
exception reaches your code, the situation is severe. Back off for a longer
period before retrying, or stagger your scripts.

```python
import time
import logging
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import RateLimitError

# Enable logging to see when 429 retries happen internally
logging.basicConfig(level=logging.WARNING)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        transactions = client.transactions.list(
            startDate="2025-06-01",
            endDate="2025-06-30",
        )
    except RateLimitError as e:
        print(f"Rate limited after retries: {e.message}")
        # All 3 built-in retries failed -- back off for 30 seconds
        time.sleep(30)
```

!!! tip
    If you regularly hit rate limits, check whether multiple processes share
    the same API ID. Stagger scheduled jobs by at least 60 seconds, or
    increase `max_retries` on the client to allow more backoff time.

### ValidationError

**When it is raised:** The API returns HTTP 400 or 422 for invalid request
parameters.

**Common causes:**

- Date format `"06/01/2025"` instead of the required `"2025-06-01"` (ISO 8601) -- this is the most common validation error and triggers `InvalidPayloadRequestTimestampError`
- Passing a transaction type string that does not exist to `list_by_type()` (e.g., `"membership"` instead of `"recurring"`)
- Sending `endDate` earlier than `startDate`
- Malformed JSON in the request body (rare with the SDK, but possible if you modify internals)
- Missing required parameters on endpoints that enforce them

**Recommended handling:** Do not retry -- fix the request parameters. Check date
formats (`YYYY-MM-DD`), parameter names, and allowed values. Use `error_type` to
distinguish between timestamp errors and general payload errors.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import ValidationError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        transactions = client.transactions.list(
            startDate="06/01/2025",  # Wrong format!
            endDate="06/30/2025",
        )
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        print(f"Error type: {e.error_type}")

        if e.error_type == "InvalidPayloadRequestTimestampError":
            print("Fix date format to YYYY-MM-DD")
        elif e.error_type == "PayloadValidationError":
            print("Check parameter names and values")
```

!!! info
    The `PayloadValidationError` type may return multiple error messages in the
    response body. The SDK joins them into a single `message` string separated
    by semicolons. Check `e.body` for the original `"messages"` array if you
    need to inspect each validation failure individually.

### NotFoundError

**When it is raised:** The API returns HTTP 404 when the requested resource does
not exist.

**Common causes:**

- Transaction ID from a different site than the one configured via `site_code` -- IDs are scoped per site
- Customer ID that was valid in one database but does not exist in another (e.g., looking up a WashU customer ID against the Icon database)
- Deleted recurring account or gift card that no longer exists in the system
- Typo or truncated ID string

**Recommended handling:** Verify the ID is correct and belongs to the configured
site. In batch workflows where you iterate over a list of IDs, catch
`NotFoundError` and skip or log the missing record rather than aborting the
entire loop.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import NotFoundError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    # Gracefully handle missing records in a batch lookup
    customer_ids = ["12345", "99999", "67890"]
    found = []

    for cid in customer_ids:
        try:
            customer = client.customers.get(cid)
            found.append(customer)
        except NotFoundError:
            print(f"Customer {cid} not found, skipping")
            # e.error_type will be "EntityNotFoundError"

    print(f"Found {len(found)} of {len(customer_ids)} customers")
```

### ServerError

**When it is raised:** The API returns HTTP 5xx indicating a server-side
failure.

**Common causes:**

- Sonny's API scheduled maintenance window -- the API may return 500 or 503 during planned updates
- Intermittent 500 errors on large date-range queries or `load_job()` requests that stress the backend
- `ServerUnexpectedFailure` -- an unexpected crash on the API side
- 502/503 responses from upstream infrastructure (load balancer, gateway)

**Recommended handling:** Retry after a delay. Server errors are often transient.
If they persist beyond a few minutes, check with Sonny's support for known
outages. For automated pipelines, implement retry with backoff (see
[Custom Retry Patterns](#custom-retry-patterns)).

```python
import time
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import ServerError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            transactions = client.transactions.list(
                startDate="2025-06-01",
                endDate="2025-06-30",
            )
            break  # Success
        except ServerError as e:
            print(f"Server error ({e.status_code}): {e.message}")
            if attempt < max_attempts - 1:
                delay = 5 * (2 ** attempt)
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print("All retries exhausted")
                raise
```

### APIConnectionError

**When it is raised:** The HTTP request fails before reaching the server --
no response is received.

**Common causes:**

- No internet connection on the machine running the script
- DNS resolution failure for `trigonapi.sonnyscontrols.com` -- common on new server deployments where DNS is not yet configured
- Corporate firewall or proxy blocking outbound HTTPS traffic to the Sonny's API domain
- VPN disconnection mid-request
- Running inside a Docker container or CI environment without outbound network access

**Recommended handling:** Check network connectivity. This error does not have
`status_code` or `body` attributes since no HTTP response was received. For
automated pipelines, retry a few times with a delay -- the network issue may be
transient.

```python
import time
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APIConnectionError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        sites = client.sites.list()
    except APIConnectionError as e:
        print(f"Connection failed: {e.message}")
        print("Troubleshooting steps:")
        print("  1. Check internet connectivity")
        print("  2. Verify DNS resolves: nslookup trigonapi.sonnyscontrols.com")
        print("  3. Check firewall allows HTTPS to trigonapi.sonnyscontrols.com")
        print("  4. If behind a proxy, configure requests proxy settings")
```

### APITimeoutError

**When it is raised:** The HTTP request was sent but no response arrived within
the timeout period. Also raised when `load_job()` polling exceeds the configured
`timeout`.

**Common causes:**

- `load_job()` on a high-volume site with a full day of transactions -- the batch job takes longer than the default 300-second timeout to complete
- Very large `list()` or `list_v2()` queries spanning months of data at a busy site
- Network congestion or high latency between your server and `trigonapi.sonnyscontrols.com`
- API under heavy load from other consumers during peak hours

**Recommended handling:** For `load_job()`, increase the `timeout` parameter or
use a shorter date range. For list methods, narrow the date range. Consider
splitting multi-month queries into smaller chunks.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APITimeoutError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        # Large export that may time out
        results = client.transactions.load_job(
            startDate="2025-06-01",
            endDate="2025-06-02",
            timeout=600.0,  # 10 minutes instead of default 5
        )
    except APITimeoutError:
        print("Job timed out -- try a shorter date range or increase timeout")
        # Fallback: split into smaller chunks
        from datetime import date, timedelta
        start = date(2025, 6, 1)
        end = date(2025, 6, 2)
        midpoint = start + (end - start) / 2
        print(f"Try splitting: {start} to {midpoint} and {midpoint} to {end}")
```

!!! note
    `APITimeoutError` is a subclass of `APIConnectionError`. If you catch
    `APIConnectionError`, it will also catch timeouts. Use the specific
    `APITimeoutError` class when you need to distinguish timeouts from other
    connection failures.

## Built-in Retry Behavior

The SDK includes two layers of automatic protection against rate limiting.

### Pre-request rate limiting

Every request passes through a sliding window rate limiter before it is sent.
The limiter enforces a maximum of **20 requests per 15-second window**. If you
are at capacity, the client automatically sleeps until a slot opens -- no
exception is raised.

### 429 retry with exponential backoff

If the API returns HTTP 429 despite the client-side limiter (e.g., another
script shares the same API ID), the SDK retries with exponential backoff:

| Attempt | Delay  |
|---------|--------|
| 1       | 1 second  |
| 2       | 2 seconds |
| 3       | 4 seconds |

After `max_retries` attempts (default 3), the SDK raises `RateLimitError`.

!!! note
    You can configure `max_retries` when constructing the client:

    ```python
    client = SonnysClient(
        api_id="your-api-id",
        api_key="your-api-key",
        max_retries=5,  # Allow up to 5 retry attempts for 429s
    )
    ```

### What is NOT retried automatically

The SDK only retries HTTP 429 responses. These errors are **not** retried:

- **`APIConnectionError`** -- Network failures (no response received)
- **`APITimeoutError`** -- Request timeouts
- **`AuthError`** (403) -- Credential or authorization problems
- **`ValidationError`** (400/422) -- Invalid request parameters
- **`NotFoundError`** (404) -- Resource does not exist
- **`ServerError`** (5xx) -- Server-side failures

If you need retry logic for these errors, implement it yourself using the
patterns below.

## Custom Retry Patterns

### Retry on transient server errors

Server errors (500, 502, 503) are often transient. Wrap your call in a simple
retry loop with backoff:

```python
import time
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import ServerError

def fetch_with_retry(client, retries=3, base_delay=2.0):
    for attempt in range(retries):
        try:
            return client.transactions.list(
                startDate="2025-06-01",
                endDate="2025-06-30",
            )
        except ServerError as e:
            if attempt == retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Server error ({e.status_code}), retrying in {delay}s...")
            time.sleep(delay)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    transactions = fetch_with_retry(client)
```

### Retry on connection and timeout errors

Network problems can be intermittent. Retry `APIConnectionError` and
`APITimeoutError` with a short delay:

```python
import time
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APIConnectionError, APITimeoutError

def fetch_with_network_retry(client, retries=3, delay=5.0):
    for attempt in range(retries):
        try:
            return client.customers.list()
        except (APIConnectionError, APITimeoutError) as e:
            if attempt == retries - 1:
                raise
            print(f"{type(e).__name__}, retrying in {delay}s...")
            time.sleep(delay)

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    customers = fetch_with_network_retry(client)
```

### Production retry with tenacity

For production systems, use the `tenacity` library for configurable,
decorator-based retry logic:

```
pip install tenacity
```

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APIConnectionError, APITimeoutError, ServerError

@retry(
    retry=retry_if_exception_type((ServerError, APIConnectionError, APITimeoutError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def fetch_transactions(client):
    return client.transactions.list(
        startDate="2025-06-01",
        endDate="2025-06-30",
    )

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    transactions = fetch_transactions(client)
```

!!! warning
    Never retry `AuthError` or `ValidationError` -- these indicate a code or
    configuration problem, not a transient failure. Retrying them wastes time
    and rate limit budget without any chance of success.

## Quick Reference

A scannable cheat sheet mapping HTTP status codes to SDK exceptions, typical
causes, and recommended actions.

| HTTP Status | SDK Exception        | Typical Cause                                      | Recommended Action                          |
|-------------|----------------------|----------------------------------------------------|---------------------------------------------|
| --          | `APIConnectionError` | Network down, DNS failure, firewall blocking        | Check connectivity; retry with delay        |
| --          | `APITimeoutError`    | Slow response, large query, job polling timeout     | Shorten date range; increase timeout        |
| 400         | `ValidationError`    | Bad date format, invalid parameters                 | Fix request parameters; do not retry        |
| 403         | `AuthError`          | Wrong credentials, unauthorized site code           | Fix credentials or site_code; do not retry  |
| 404         | `NotFoundError`      | ID does not exist, wrong site, deleted record       | Verify ID and site; skip in batch loops     |
| 422         | `ValidationError`    | Payload validation failure                          | Check parameter values; do not retry        |
| 429         | `RateLimitError`     | Rate limit exceeded after built-in retries          | Back off 30s+; stagger concurrent scripts   |
| 500         | `ServerError`        | API crash, maintenance, `ServerUnexpectedFailure`   | Retry with backoff; contact support if persistent |
| 502/503     | `ServerError`        | Gateway/infrastructure error                        | Retry with backoff; usually transient       |
