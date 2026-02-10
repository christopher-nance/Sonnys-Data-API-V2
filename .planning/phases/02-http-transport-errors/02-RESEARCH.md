# Phase 2: HTTP Transport & Errors - Research

**Researched:** 2026-02-10
**Domain:** Python API client HTTP transport layer + exception hierarchy
**Confidence:** HIGH

<research_summary>
## Summary

Researched how production Python API client libraries (OpenAI, Stripe) implement HTTP transport, exception hierarchies, and error mapping. Cross-referenced with the Sonny's OpenAPI spec (`bo-data-open-api.yml` v0.2.0) and existing Data Fetcher notebook for actual API response shapes.

The standard approach uses the OpenAI/Stainless pattern: a single `_request()` method on the client that handles all HTTP communication, retry logic, and error classification. The exception hierarchy follows a two-branch tree: `APIConnectionError` (no response) vs `APIStatusError` (got error response), with status-specific leaf exceptions. Error mapping uses status code dispatch with body field extraction.

Key findings from the OpenAPI spec:
- **Error responses** are flat JSON objects with a required `type` field (string enum) and a `message` field. NOT wrapped in an `{"error": {...}}` envelope. Example: `{"type": "MissingClientCredentialsError", "message": "..."}`.
- **`PayloadValidationError`** uses `messages` (plural, array of strings) instead of `message`.
- **`ServerUnexpectedFailure`** includes an additional `code` field (string, e.g., `"SCEC0001"`).
- **Successful responses** wrap data in `{"data": {...}}` with list endpoints including `offset`, `limit`, and `total` pagination fields inside the `data` object.
- **13 total error types** across 5 HTTP status codes (403, 429, 400, 422, 404, 500).

**Primary recommendation:** Use OpenAI-style exception hierarchy with `SonnysError → APIError → APIConnectionError/APIStatusError → specific`. Map error types using HTTP status code first, store the Sonny's `type` string on the exception's `error_type` field for callers who need sub-type distinction (especially the 7 different 403 error types).
</research_summary>

<standard_stack>
## Standard Stack

### Core (already established in Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.32.5 | HTTP client | De facto sync HTTP, Session for connection pooling + persistent headers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging (stdlib) | N/A | Request/response debug logging | Always — callers configure level |
| time (stdlib) | N/A | Retry backoff sleep | In `_request()` retry loop |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests.Session | httpx.Client | httpx supports async but scope is sync-only; requests simpler |
| Custom retry in `_request()` | urllib3.Retry via HTTPAdapter | urllib3.Retry is coarser — can't distinguish Sonny's error types for retry decisions |
| Manual status check | response.raise_for_status() | raise_for_status discards error body; need body to map error types |

**Installation:**
Already installed from Phase 1 — no new dependencies.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Single `_request()` Method (OpenAI/Stainless)
**What:** All HTTP communication flows through one `_request()` method on the client. It handles: build URL → send request → catch connection errors → check status → retry if needed → parse error → return data.
**When to use:** Always — this is the entry point for all resource classes.
**Why chosen:** Used by OpenAI, Anthropic, and Stripe SDKs. Single place to handle auth, timeouts, retries, logging, and error mapping. Resources call `self._client._request()` and get back parsed data or a typed exception.

**Example:**
```python
# On SonnysClient
def _request(
    self,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    url = f"{self.BASE_URL}/{path.lstrip('/')}"
    try:
        response = self._session.request(
            method, url, params=params, json=json,
            timeout=timeout or self._timeout,
        )
    except requests.Timeout as err:
        raise APITimeoutError() from err
    except requests.ConnectionError as err:
        raise APIConnectionError(str(err)) from err

    if not (200 <= response.status_code < 300):
        raise self._make_status_error(response)

    return response.json()
```

### Pattern 2: Two-Branch Exception Hierarchy (OpenAI)
**What:** Base `APIError` splits into `APIConnectionError` (no HTTP response at all) and `APIStatusError` (got an HTTP error response). Status-specific exceptions are leaf nodes under `APIStatusError`.
**When to use:** Always — this is the cleanest pattern for typed error handling.
**Why chosen:** Enables `except APIConnectionError` to catch all network failures, `except APIStatusError` to catch all HTTP errors, and specific catches like `except RateLimitError`. OpenAI pattern is cleaner than Stripe's flat hierarchy.

```
SonnysError (root — catches everything from this SDK)
├── APIError (all API interaction errors)
│   ├── APIConnectionError (no response received)
│   │   └── APITimeoutError (timeout specifically)
│   └── APIStatusError (HTTP error response received)
│       ├── AuthError (403 — all Sonny's auth error types)
│       ├── RateLimitError (429 — RequestRateExceedError)
│       ├── ValidationError (400/422 — payload validation errors)
│       ├── NotFoundError (404 — EntityNotFoundError)
│       └── ServerError (500 — ServerUnexpectedFailure)
```

### Pattern 3: Status Code + Error Type Dispatch
**What:** Map HTTP status code to exception class first, then store the API's `type` string from the response body on the exception for sub-type discrimination. This handles Sonny's case where 7 different error types share HTTP 403.
**When to use:** In `_make_status_error()` when building the exception from a response.

**Verified error response format (from OpenAPI spec):**
```json
// All errors are flat JSON with required "type" field:
{"type": "MissingClientCredentialsError", "message": "One or more of the required header..."}

// PayloadValidationError uses "messages" (plural, array):
{"type": "PayloadValidationError", "messages": ["The request payload is well formed..."]}

// ServerUnexpectedFailure includes a "code" field:
{"type": "ServerUnexpectedFailure", "message": "An unexpected error has occurred.", "code": "SCEC0001"}
```

**Complete error type → HTTP status mapping (from OpenAPI spec):**

| HTTP Status | Error Types | Maps To |
|-------------|-------------|---------|
| 403 | MissingClientCredentialsError, BadClientCredentialsError, MismatchCredentialsError, NotAuthorizedError, BadSiteCredentialsError, NotAuthorizedSiteCredentialsError, NotAuthorizedSiteArgsError | AuthError |
| 429 | RequestRateExceedError | RateLimitError |
| 400 | InvalidPayloadRequestTimestampError, UnexpectedFailure | ValidationError / APIError |
| 422 | PayloadValidationError | ValidationError |
| 404 | EntityNotFoundError | NotFoundError |
| 500 | ServerUnexpectedFailure | ServerError |

```python
def _make_status_error(self, response: requests.Response) -> APIStatusError:
    body = self._parse_error_body(response)
    error_type = body.get("type", "") if isinstance(body, dict) else ""
    # message field; PayloadValidationError uses "messages" (array)
    message = body.get("message") or ""
    if not message and "messages" in body:
        message = "; ".join(body["messages"])
    message = message or f"HTTP {response.status_code}"

    if response.status_code == 403:
        return AuthError(message=message, ...)
    elif response.status_code == 429:
        return RateLimitError(message=message, ...)
    elif response.status_code in (400, 422):
        return ValidationError(message=message, ...)
    elif response.status_code == 404:
        return NotFoundError(message=message, ...)
    elif response.status_code >= 500:
        return ServerError(message=message, ...)
    else:
        return APIStatusError(message=message, ...)
```

### Pattern 4: Debug Logging at Transport Level
**What:** Log request method/path at DEBUG level, log response status at DEBUG level, log full request/response bodies at a lower level (or gated behind a flag). Uses Python stdlib `logging` so callers control verbosity.
**When to use:** Always — essential for debugging API issues.

```python
import logging

log = logging.getLogger("sonnys_data_client")

# In _request():
log.debug("Request: %s %s", method, url)
log.debug("Response: %s %s", response.status_code, url)
```

### Anti-Patterns to Avoid
- **Using `raise_for_status()`:** Discards the error body before you can parse it. Manual status check is required.
- **No default timeout:** `requests` defaults to `None` (wait forever). Always set a timeout.
- **Retrying inside resource methods:** Retry logic belongs in `_request()`, not scattered across resource classes.
- **Catching bare `Exception`:** Always catch specific `requests` exceptions (`Timeout`, `ConnectionError`).
- **Flat exception hierarchy (Stripe legacy):** Makes it impossible to catch "all errors with an HTTP response" vs "all network errors" with a single except clause.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP connection pooling | Manual connection management | `requests.Session` | Handles keep-alive, connection reuse, persistent headers |
| Timeout handling | Manual socket timeouts | `requests` timeout parameter | Tuple of (connect, read) timeout; well-tested |
| JSON parsing | Manual string parsing | `response.json()` | Handles encoding, content-type, raises ValueError on bad JSON |
| Exponential backoff formula | Custom sleep logic | Standard formula: `min(0.5 * 2^attempt, 8.0) * jitter` | Industry standard used by OpenAI + Stripe |
| Error body extraction | Ad-hoc dict access | Centralized `_parse_error_body()` | One place to handle JSON parse failures, missing fields |

**Key insight:** The HTTP transport layer is commodity infrastructure. The value-add is mapping Sonny's specific error types to a clean exception hierarchy. Don't over-engineer the transport — requests.Session + a single `_request()` method is the proven pattern.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: No Default Timeout
**What goes wrong:** Client hangs indefinitely when the API is unresponsive.
**Why it happens:** `requests` default timeout is `None` (wait forever).
**How to avoid:** Always set a default timeout on the client. Use tuple form `(connect_timeout, read_timeout)`. Standard: `(3.05, 30)` — 3.05s connect aligns with TCP retransmission window, 30s read for most endpoints.
**Warning signs:** Requests that never return during API outages.

### Pitfall 2: Not Preserving Error Body
**What goes wrong:** Exception is raised but the Sonny's error type string is lost.
**Why it happens:** Using `raise_for_status()` or raising before parsing the response body.
**How to avoid:** Always parse `response.json()` before raising. Store the parsed body on the exception object. Handle JSON parse failures gracefully (API might return HTML on 5xx).
**Warning signs:** Exception messages say "403 Forbidden" with no indication of which of the 7 Sonny's 403 error types triggered it.

### Pitfall 3: Retrying Non-Idempotent Requests Blindly
**What goes wrong:** POST to `/transaction/load-job` gets retried, creating duplicate batch jobs.
**Why it happens:** Retry logic doesn't distinguish GET from POST.
**How to avoid:** Only auto-retry on GET requests and connection errors. For POST, only retry on connection errors where the request was never sent (not on 5xx responses, which means the server received it). Or — limit retries to specific status codes (408, 429, 5xx) where the server explicitly signals retry-ability.
**Warning signs:** Duplicate resources created in production.

### Pitfall 4: Rate Limit Error vs Rate Limiter Confusion
**What goes wrong:** The exception hierarchy's `RateLimitError` (HTTP 429 response) gets confused with the rate limiter (Phase 3, proactive throttling).
**Why it happens:** Both deal with "rate limits" but serve different purposes.
**How to avoid:** Clear naming: `RateLimitError` is the exception raised when the API returns 429. The rate limiter (Phase 3) is a separate class that prevents hitting the limit in the first place. If the rate limiter is working correctly, `RateLimitError` should rarely be raised — it's a safety net.
**Warning signs:** Unclear which layer is controlling request rate.

### Pitfall 5: Not Handling Non-JSON Error Responses
**What goes wrong:** `response.json()` raises `ValueError` on 5xx responses that return HTML error pages.
**Why it happens:** Server errors (nginx 502, load balancer 503) often return HTML, not JSON.
**How to avoid:** Wrap `response.json()` in try/except. Fall back to `response.text` for the error message.
**Warning signs:** Unhandled `ValueError` exceptions from response parsing.
</common_pitfalls>

<code_examples>
## Code Examples

### Exception Hierarchy (OpenAI pattern adapted for Sonny's)
```python
# Source: Pattern from openai-python _exceptions.py, adapted for Sonny's error types
# Error type field is "type" (verified from OpenAPI BaseError schema)
class SonnysError(Exception):
    """Root exception for the sonnys-data-client SDK."""

class APIError(SonnysError):
    """Base for all API interaction errors."""
    message: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

class APIConnectionError(APIError):
    """Network failure — no HTTP response received."""
    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)

class APITimeoutError(APIConnectionError):
    """Request timed out."""
    def __init__(self) -> None:
        super().__init__("Request timed out.")

class APIStatusError(APIError):
    """API returned a non-2xx HTTP response."""
    status_code: int
    body: dict | None
    error_type: str | None  # Sonny's "type" field from BaseError schema

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: dict | None = None,
        error_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.error_type = error_type

# Leaf exceptions matching PROJECT.md mapping
class AuthError(APIStatusError):
    """403 — 7 credential/authorization error types."""
    # error_type distinguishes: MissingClientCredentialsError, BadClientCredentialsError,
    # MismatchCredentialsError, NotAuthorizedError, BadSiteCredentialsError,
    # NotAuthorizedSiteCredentialsError, NotAuthorizedSiteArgsError

class RateLimitError(APIStatusError):
    """429 — RequestRateExceedError."""

class ValidationError(APIStatusError):
    """400/422 — PayloadValidationError, InvalidPayloadRequestTimestampError."""
    # Note: PayloadValidationError uses "messages" (array) not "message"

class NotFoundError(APIStatusError):
    """404 — EntityNotFoundError."""

class ServerError(APIStatusError):
    """500 — ServerUnexpectedFailure (includes extra "code" field in body)."""
```

### Error Body Parsing (verified against OpenAPI spec)
```python
# Sonny's errors are flat JSON: {"type": "...", "message": "..."}
# No {"error": {...}} envelope — simpler than OpenAI/Stripe pattern.
def _parse_error_body(self, response: requests.Response) -> dict:
    """Parse error response body, handling non-JSON gracefully."""
    try:
        body = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        # 5xx may return HTML; fall back to text
        return {"type": "Unknown", "message": response.text or f"HTTP {response.status_code}"}

    return body if isinstance(body, dict) else {"type": "Unknown", "message": str(body)}
```

### `_request()` Method (core transport)
```python
# Source: Pattern from openai-python, adapted for requests library
import logging

log = logging.getLogger("sonnys_data_client")

DEFAULT_TIMEOUT = (3.05, 30)  # (connect, read)

def _request(
    self,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    timeout: float | tuple[float, float] | None = None,
) -> dict[str, Any]:
    url = f"{self.BASE_URL}/{path.lstrip('/')}"
    effective_timeout = timeout or self._timeout

    log.debug("%s %s", method, url)

    try:
        response = self._session.request(
            method, url,
            params=params,
            json=json,
            timeout=effective_timeout,
        )
    except requests.Timeout as err:
        raise APITimeoutError() from err
    except requests.ConnectionError as err:
        raise APIConnectionError(str(err)) from err

    log.debug("Response %s %s", response.status_code, url)

    if not (200 <= response.status_code < 300):
        raise self._make_status_error(response)

    return response.json()
```

### Status Code → Exception Mapping (verified against OpenAPI spec)
```python
# Sonny's error type field is "type" (confirmed from BaseError schema)
_STATUS_MAP: dict[int, type[APIStatusError]] = {
    400: ValidationError,   # InvalidPayloadRequestTimestampError, UnexpectedFailure
    403: AuthError,         # 7 auth/credential error types
    404: NotFoundError,     # EntityNotFoundError
    422: ValidationError,   # PayloadValidationError (note: uses "messages" array)
    429: RateLimitError,    # RequestRateExceedError
    500: ServerError,       # ServerUnexpectedFailure (has extra "code" field)
}

def _make_status_error(self, response: requests.Response) -> APIStatusError:
    body = self._parse_error_body(response)
    error_type = body.get("type", "")
    # Handle both "message" (string) and "messages" (array, PayloadValidationError)
    message = body.get("message", "")
    if not message and "messages" in body:
        message = "; ".join(body["messages"])
    message = message or f"HTTP {response.status_code}"

    exc_class = _STATUS_MAP.get(response.status_code)
    if exc_class is None:
        exc_class = ServerError if response.status_code >= 500 else APIStatusError

    return exc_class(
        message,
        status_code=response.status_code,
        body=body,
        error_type=error_type,
    )
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat exception hierarchy (Stripe v7) | Two-branch tree (OpenAI/Stainless) | 2023+ | Cleaner catch semantics: `except APIConnectionError` vs `except APIStatusError` |
| `raise_for_status()` | Manual status check + body parse | Always was better | Preserves error body for typed exceptions |
| No default timeout | Always `(connect, read)` tuple | Best practice | Prevents hanging on API outages |
| urllib3.Retry via HTTPAdapter | Custom retry in `_request()` | 2023+ (OpenAI pattern) | Finer control over which errors/statuses to retry |
| Module-level error handlers | Per-instance in client `_request()` | 2023+ | Thread-safe, supports multiple client instances |

**New tools/patterns to consider:**
- **`error_type` field on exceptions**: Store the API's error type string (e.g., `MissingClientCredentialsError`) for callers who need to distinguish between sub-types of the same HTTP status.
- **`body` field on exceptions**: Store the full parsed error body for debugging and support escalation.

**Deprecated/outdated:**
- **Flat exception hierarchies**: Stripe's legacy pattern where all errors inherit from StripeError directly.
- **`raise_for_status()` in SDK clients**: Never appropriate for API clients that need to parse error bodies.
</sota_updates>

<open_questions>
## Open Questions

1. **~~Exact Sonny's error response JSON body format~~ RESOLVED**
   - **Confirmed from OpenAPI spec:** Flat JSON with required `type` field (string enum from BaseError schema) and `message` field (string). No `{"error": {...}}` envelope. `PayloadValidationError` uses `messages` (array). `ServerUnexpectedFailure` has extra `code` field.

2. **Whether the API returns `Retry-After` header on 429 responses**
   - What we know: 429 status code is returned for `RequestRateExceedError`. Rate limit is 20 req/15s. OpenAPI spec doesn't mention `Retry-After` header.
   - What's unclear: Whether the header is present in actual responses (not always documented in specs).
   - Recommendation: Check for `Retry-After` header and respect it if present (cap at 60s). If not present, fall back to 15s wait (the full rate limit window). Validate during integration testing.

3. **~~Successful response envelope consistency~~ RESOLVED**
   - **Confirmed from OpenAPI spec:** All successful responses wrap data in `{"data": {...}}`. List endpoints include `offset`, `limit`, and `total` pagination fields inside the `data` object alongside the resource array. Detail endpoints return `{"data": <object>}` directly. `_request()` should return the raw parsed JSON and let the resource layer (Phase 5) unwrap the envelope.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- **Sonny's OpenAPI Spec v0.2.0** (`bo-data-open-api.yml`) — BaseError schema, all 13 error type schemas, response envelope format, field names/types. Authoritative source for API behavior.
- [OpenAI Python SDK - _exceptions.py](https://github.com/openai/openai-python) — exception hierarchy, field choices, __init__ patterns
- [OpenAI Python SDK - _base_client.py](https://github.com/openai/openai-python) — `_request()` flow, error mapping, retry logic
- [Stripe Python SDK - _error.py](https://github.com/stripe/stripe-python) — exception fields, error body parsing
- [Stripe Python SDK - _http_client.py](https://github.com/stripe/stripe-python) — retry strategy, backoff formula
- Existing notebook: `WashMetrix Data Query/Sonnys Data Fetcher.ipynb` — verified response envelope `{"data": {...}}`, auth headers, 429 handling

### Secondary (MEDIUM confidence)
- PROJECT.md error types table — 13 error types with HTTP status codes and client exception mappings
- [requests library documentation](https://docs.python-requests.org/en/latest/user/advanced/) — Session usage, timeout patterns
- [DeepWiki: openai/openai-python](https://deepwiki.com/openai/openai-python) — architecture analysis
- [DeepWiki: stripe/stripe-python](https://deepwiki.com/stripe/stripe-python) — architecture analysis

### Tertiary (LOW confidence — needs validation during implementation)
- `Retry-After` header on 429 responses — not documented in OpenAPI spec, needs live testing
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: requests.Session HTTP transport
- Ecosystem: Python stdlib logging, exception hierarchy patterns
- Patterns: OpenAI `_request()` method, two-branch exception tree, status code dispatch
- Pitfalls: Missing timeouts, lost error bodies, non-JSON errors, POST retry safety

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, requests usage well-understood
- Architecture: HIGH — patterns verified from OpenAI + Stripe production SDKs
- Exception hierarchy: HIGH — OpenAI pattern is well-documented and battle-tested
- Error mapping: HIGH — exact error body format verified from OpenAPI spec (BaseError schema with `type` field)
- Code examples: HIGH — derived from OpenAI/Stripe source code, adapted for requests library and verified Sonny's API format

**Research date:** 2026-02-10
**Valid until:** 2026-03-12 (30 days — patterns are stable)
</metadata>

---

*Phase: 02-http-transport-errors*
*Research completed: 2026-02-10*
*Ready for planning: yes*
