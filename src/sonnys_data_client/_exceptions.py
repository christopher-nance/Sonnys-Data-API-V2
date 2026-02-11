"""Exception hierarchy for the Sonny's Data Client SDK."""

from __future__ import annotations

import requests


class SonnysError(Exception):
    """Base exception for all Sonny's Data Client errors."""


class APIError(SonnysError):
    """An error returned by the API.

    Attributes:
        message: Human-readable error description.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class APIConnectionError(APIError):
    """Failed to connect to the Sonny's Data API."""

    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    """Request to the Sonny's Data API timed out."""

    def __init__(self, message: str = "Request timed out.") -> None:
        super().__init__(message)


class APIStatusError(APIError):
    """API returned an error HTTP status.

    Attributes:
        status_code: The HTTP status code returned by the API.
        body: The parsed JSON error body, if available.
        error_type: The Sonny's API error type string, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: dict | None = None,
        error_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.error_type = error_type
        super().__init__(message)

    def __str__(self) -> str:
        header = f"[HTTP {self.status_code}]"
        if self.error_type:
            header += f" ({self.error_type})"
        result = f"{header} {self.message}"
        if self.body:
            result += f"\nAPI response body: {self.body}"
        return result


class AuthError(APIStatusError):
    """Authentication or authorization failed (HTTP 403).

    Raised for invalid/missing API credentials or unauthorized site access.
    """


class RateLimitError(APIStatusError):
    """Rate limit exceeded (HTTP 429).

    The client auto-retries with backoff, so this is only raised after
    retries are exhausted.
    """


class ValidationError(APIStatusError):
    """Request validation failed (HTTP 400/422).

    Check ``error_type`` and ``body`` for details on invalid parameters.
    """


class NotFoundError(APIStatusError):
    """Requested resource not found (HTTP 404)."""


class ServerError(APIStatusError):
    """Sonny's API server error (HTTP 500+)."""


# ---------------------------------------------------------------------------
# Status code to exception class mapping
# ---------------------------------------------------------------------------

_STATUS_MAP: dict[int, type[APIStatusError]] = {
    400: ValidationError,
    403: AuthError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
    500: ServerError,
}


# ---------------------------------------------------------------------------
# Error body parsing and status-code-to-exception mapping
# ---------------------------------------------------------------------------


def parse_error_body(response: requests.Response) -> dict:
    """Parse error response body, handling non-JSON gracefully.

    Returns a dict with at least ``type`` and ``message`` keys.
    """
    try:
        body = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        text = response.text or f"HTTP {response.status_code}"
        return {"type": "Unknown", "message": text}

    if isinstance(body, dict):
        return body

    return {"type": "Unknown", "message": str(body)}


def make_status_error(response: requests.Response) -> APIStatusError:
    """Build the appropriate ``APIStatusError`` subclass from an HTTP response.

    Uses the status code to select the exception class and extracts the
    Sonny's ``type`` field as ``error_type``.
    """
    body = parse_error_body(response)
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
