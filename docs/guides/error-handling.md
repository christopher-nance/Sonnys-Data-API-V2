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

- Wrong `api_id` or `api_key` values
- `site_code` not authorized for the given API ID
- Missing credentials (headers not sent)
- API ID does not have permission for the requested resource

**Recommended handling:** Do not retry -- fix your credentials or site code
configuration. Check that your `api_id`, `api_key`, and `site_code` match what
was provisioned by Sonny's.

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
        # Common error_type values:
        #   BadClientCredentialsError -- wrong api_id or api_key
        #   NotAuthorizedSiteCredentialsError -- site_code not authorized
        #   MissingClientCredentialsError -- credentials not provided
```

### RateLimitError

**When it is raised:** The API returns HTTP 429 and all built-in retries have
been exhausted.

**Common causes:**

- Running multiple scripts against the same API ID simultaneously
- Burst traffic exceeding 20 requests per 15-second window
- Bulk export without rate awareness alongside scheduled automation

**Recommended handling:** The SDK already retries 429 responses with exponential
backoff (see [Built-in Retry Behavior](#built-in-retry-behavior)). If this
exception reaches your code, the situation is severe. Back off for a longer
period before retrying, or stagger your scripts.

```python
import time
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import RateLimitError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        transactions = client.transactions.list(
            startDate="2025-06-01",
            endDate="2025-06-30",
        )
    except RateLimitError as e:
        print(f"Rate limited after retries: {e.message}")
        # Back off and retry manually
        time.sleep(30)
```

### ValidationError

**When it is raised:** The API returns HTTP 400 or 422 for invalid request
parameters.

**Common causes:**

- Incorrect date format (e.g., `"06/01/2025"` instead of `"2025-06-01"`)
- Invalid or unrecognized query parameter values
- Missing required parameters
- Requesting a transaction type that does not exist

**Recommended handling:** Do not retry -- fix the request parameters. Check date
formats (`YYYY-MM-DD`), parameter names, and allowed values.

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
        # Fix: use YYYY-MM-DD format
        # e.error_type will be "InvalidPayloadRequestTimestampError"
        # or "PayloadValidationError"
```

### NotFoundError

**When it is raised:** The API returns HTTP 404 when the requested resource does
not exist.

**Common causes:**

- Transaction ID, customer ID, or account ID does not exist
- ID belongs to a different site than the one configured
- Record was deleted or never existed

**Recommended handling:** Verify the ID is correct and belongs to the configured
site. Consider handling this gracefully in loops where some IDs may be stale.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import NotFoundError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        customer = client.customers.get("99999")
    except NotFoundError as e:
        print(f"Customer not found: {e.message}")
        # e.error_type will be "EntityNotFoundError"
```

### ServerError

**When it is raised:** The API returns HTTP 5xx indicating a server-side
failure.

**Common causes:**

- Sonny's API maintenance window
- Intermittent 500 errors on large or complex queries
- Temporary infrastructure issues

**Recommended handling:** Retry after a delay. Server errors are often transient.
If they persist, contact Sonny's support.

```python
import time
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import ServerError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        transactions = client.transactions.list(
            startDate="2025-06-01",
            endDate="2025-06-30",
        )
    except ServerError as e:
        print(f"Server error ({e.status_code}): {e.message}")
        # Retry after a delay
        time.sleep(10)
```

### APIConnectionError

**When it is raised:** The HTTP request fails before reaching the server --
no response is received.

**Common causes:**

- No internet connection
- DNS resolution failure for `trigonapi.sonnyscontrols.com`
- Corporate firewall blocking outbound HTTPS traffic
- Proxy misconfiguration

**Recommended handling:** Check network connectivity. This error does not have
`status_code` or `body` attributes since no HTTP response was received.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APIConnectionError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        sites = client.sites.list()
    except APIConnectionError as e:
        print(f"Connection failed: {e.message}")
        # Check network, DNS, firewall settings
```

### APITimeoutError

**When it is raised:** The HTTP request was sent but no response arrived within
the timeout period.

**Common causes:**

- Slow API response under heavy load
- Very large query result sets
- `load_job()` polling exceeding the configured timeout
- Network congestion or high latency

**Recommended handling:** Retry with a shorter date range or increase the timeout.
For `load_job()`, use a shorter date range or increase the `timeout` parameter.

```python
from sonnys_data_client import SonnysClient
from sonnys_data_client._exceptions import APITimeoutError

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    try:
        results = client.transactions.load_job(
            startDate="2025-06-01",
            endDate="2025-06-02",
            timeout=600.0,
        )
    except APITimeoutError:
        print("Request timed out -- try a shorter date range")
```

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
