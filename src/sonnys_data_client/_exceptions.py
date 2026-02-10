"""Exception hierarchy for the Sonny's Data Client SDK."""

from __future__ import annotations

import requests


class SonnysError(Exception):
    pass


class APIError(SonnysError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class APIConnectionError(APIError):
    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    def __init__(self, message: str = "Request timed out.") -> None:
        super().__init__(message)


class APIStatusError(APIError):
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


class AuthError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    pass


class ValidationError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class ServerError(APIStatusError):
    pass


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
