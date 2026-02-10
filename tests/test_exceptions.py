"""Tests for error body parsing and status-code-to-exception mapping."""

import json

import requests

from sonnys_data_client._exceptions import (
    APIStatusError,
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    make_status_error,
    parse_error_body,
)


def _make_response(
    status_code: int,
    *,
    json_body: object | None = None,
    text: str | None = None,
) -> requests.models.Response:
    """Build a requests.Response for testing without making real HTTP calls."""
    resp = requests.models.Response()
    resp.status_code = status_code

    if json_body is not None:
        payload = json.dumps(json_body).encode("utf-8")
        resp._content = payload
        resp.headers["Content-Type"] = "application/json"
        resp.encoding = "utf-8"
    elif text is not None:
        resp._content = text.encode("utf-8")
        resp.headers["Content-Type"] = "text/html"
        resp.encoding = "utf-8"
    else:
        # Empty body
        resp._content = b""
        resp.encoding = "utf-8"

    return resp


# ---------------------------------------------------------------------------
# parse_error_body tests
# ---------------------------------------------------------------------------


class TestParseErrorBody:
    """Tests for parse_error_body(response)."""

    def test_json_dict_returned_as_is(self) -> None:
        """JSON body that is a dict should be returned unchanged."""
        body = {"type": "SomeError", "message": "Something went wrong"}
        resp = _make_response(400, json_body=body)

        result = parse_error_body(resp)

        assert result == body

    def test_json_string_wrapped(self) -> None:
        """JSON body that is a string should be wrapped in a standard dict."""
        resp = _make_response(400, json_body="just a string")

        result = parse_error_body(resp)

        assert result == {"type": "Unknown", "message": "just a string"}

    def test_json_array_wrapped(self) -> None:
        """JSON body that is an array should be wrapped in a standard dict."""
        resp = _make_response(400, json_body=["error1", "error2"])

        result = parse_error_body(resp)

        assert result == {"type": "Unknown", "message": "['error1', 'error2']"}

    def test_html_body_falls_back_to_text(self) -> None:
        """Non-JSON body (HTML) should fall back to response.text."""
        html = "<html><body>Bad Gateway</body></html>"
        resp = _make_response(502, text=html)

        result = parse_error_body(resp)

        assert result == {"type": "Unknown", "message": html}

    def test_empty_body_falls_back_to_status_code(self) -> None:
        """Empty body should produce message with HTTP status code."""
        resp = _make_response(503)

        result = parse_error_body(resp)

        assert result == {"type": "Unknown", "message": "HTTP 503"}


# ---------------------------------------------------------------------------
# make_status_error tests
# ---------------------------------------------------------------------------


class TestMakeStatusError:
    """Tests for make_status_error(response)."""

    def test_403_returns_auth_error(self) -> None:
        """403 with BadClientCredentialsError should return AuthError."""
        body = {"type": "BadClientCredentialsError", "message": "Invalid credentials"}
        resp = _make_response(403, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, AuthError)
        assert exc.message == "Invalid credentials"
        assert exc.status_code == 403
        assert exc.error_type == "BadClientCredentialsError"
        assert exc.body == body

    def test_429_returns_rate_limit_error(self) -> None:
        """429 with RequestRateExceedError should return RateLimitError."""
        body = {"type": "RequestRateExceedError", "message": "Rate exceeded"}
        resp = _make_response(429, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, RateLimitError)
        assert exc.message == "Rate exceeded"
        assert exc.status_code == 429
        assert exc.error_type == "RequestRateExceedError"
        assert exc.body == body

    def test_400_returns_validation_error(self) -> None:
        """400 with InvalidPayloadRequestTimestampError should return ValidationError."""
        body = {
            "type": "InvalidPayloadRequestTimestampError",
            "message": "Bad timestamp",
        }
        resp = _make_response(400, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, ValidationError)
        assert exc.message == "Bad timestamp"
        assert exc.status_code == 400
        assert exc.error_type == "InvalidPayloadRequestTimestampError"

    def test_400_unexpected_failure_returns_validation_error(self) -> None:
        """400 with UnexpectedFailure should still return ValidationError."""
        body = {"type": "UnexpectedFailure", "message": "Something went wrong"}
        resp = _make_response(400, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, ValidationError)
        assert exc.message == "Something went wrong"
        assert exc.error_type == "UnexpectedFailure"

    def test_422_payload_validation_joins_messages(self) -> None:
        """422 PayloadValidationError uses messages array joined with '; '."""
        body = {
            "type": "PayloadValidationError",
            "messages": ["Field X invalid", "Field Y required"],
        }
        resp = _make_response(422, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, ValidationError)
        assert exc.message == "Field X invalid; Field Y required"
        assert exc.status_code == 422
        assert exc.error_type == "PayloadValidationError"
        assert exc.body == body

    def test_404_returns_not_found_error(self) -> None:
        """404 with EntityNotFoundError should return NotFoundError."""
        body = {"type": "EntityNotFoundError", "message": "Not found"}
        resp = _make_response(404, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, NotFoundError)
        assert exc.message == "Not found"
        assert exc.status_code == 404
        assert exc.error_type == "EntityNotFoundError"

    def test_500_returns_server_error_with_code(self) -> None:
        """500 ServerUnexpectedFailure should return ServerError with code in body."""
        body = {
            "type": "ServerUnexpectedFailure",
            "message": "Error",
            "code": "SCEC0001",
        }
        resp = _make_response(500, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, ServerError)
        assert exc.message == "Error"
        assert exc.status_code == 500
        assert exc.error_type == "ServerUnexpectedFailure"
        assert exc.body is not None
        assert exc.body["code"] == "SCEC0001"

    def test_502_returns_server_error(self) -> None:
        """Other 5xx (502) not in STATUS_MAP should still return ServerError."""
        body = {"type": "Unknown", "message": "Bad gateway"}
        resp = _make_response(502, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, ServerError)
        assert exc.status_code == 502

    def test_503_returns_server_error(self) -> None:
        """Other 5xx (503) not in STATUS_MAP should still return ServerError."""
        body = {"type": "Unknown", "message": "Service unavailable"}
        resp = _make_response(503, json_body=body)

        exc = make_status_error(resp)

        assert isinstance(exc, ServerError)
        assert exc.status_code == 503

    def test_418_returns_base_api_status_error(self) -> None:
        """Unknown status code (418) should fall back to APIStatusError base class."""
        body = {"type": "Teapot", "message": "I am a teapot"}
        resp = _make_response(418, json_body=body)

        exc = make_status_error(resp)

        assert type(exc) is APIStatusError
        assert exc.message == "I am a teapot"
        assert exc.status_code == 418
        assert exc.error_type == "Teapot"

    def test_html_body_502_returns_server_error(self) -> None:
        """502 with HTML body should return ServerError with text as message."""
        html = "<html><body>Bad Gateway</body></html>"
        resp = _make_response(502, text=html)

        exc = make_status_error(resp)

        assert isinstance(exc, ServerError)
        assert exc.status_code == 502
        assert html in exc.message

    def test_empty_body_503_returns_server_error(self) -> None:
        """503 with empty body should return ServerError with 'HTTP 503' message."""
        resp = _make_response(503)

        exc = make_status_error(resp)

        assert isinstance(exc, ServerError)
        assert exc.status_code == 503
        assert exc.message == "HTTP 503"
