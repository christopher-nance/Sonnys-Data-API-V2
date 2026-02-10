"""Tests for SonnysClient._request method with rate limiting and 429 retry."""

import json
from unittest.mock import MagicMock, patch, call

import requests

from sonnys_data_client._client import SonnysClient
from sonnys_data_client._exceptions import (
    APIConnectionError,
    APITimeoutError,
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
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
        resp._content = b""
        resp.encoding = "utf-8"

    return resp


# ---------------------------------------------------------------------------
# Successful request tests
# ---------------------------------------------------------------------------


class TestRequestSuccess:
    """Tests for successful _request calls."""

    def test_successful_get_returns_response(self) -> None:
        """_request returns the response when status < 400."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(200, json_body={"data": "ok"})
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        result = client._request("GET", "/test")

        assert result is mock_response
        assert result.status_code == 200
        client._session.request.assert_called_once_with(
            "GET",
            "https://trigonapi.sonnyscontrols.com/v1/test",
            params=None,
        )
        client.close()

    def test_params_forwarded_to_session_request(self) -> None:
        """_request passes params dict through to session.request."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(200, json_body={"data": "ok"})
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        params = {"start": "2024-01-01", "end": "2024-01-31"}
        client._request("GET", "/data", params=params)

        client._session.request.assert_called_once_with(
            "GET",
            "https://trigonapi.sonnyscontrols.com/v1/data",
            params=params,
        )
        client.close()


# ---------------------------------------------------------------------------
# Transport error tests
# ---------------------------------------------------------------------------


class TestRequestTransportErrors:
    """Tests for transport error mapping in _request."""

    def test_connection_error_raises_api_connection_error(self) -> None:
        """requests.ConnectionError is mapped to APIConnectionError."""
        client = SonnysClient("id", "key")
        client._session.request = MagicMock(
            side_effect=requests.ConnectionError("Connection refused")
        )
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
            assert False, "Expected APIConnectionError"
        except APIConnectionError:
            pass
        finally:
            client.close()

    def test_timeout_error_raises_api_timeout_error(self) -> None:
        """requests.Timeout is mapped to APITimeoutError."""
        client = SonnysClient("id", "key")
        client._session.request = MagicMock(
            side_effect=requests.Timeout("Request timed out")
        )
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
            assert False, "Expected APITimeoutError"
        except APITimeoutError:
            pass
        finally:
            client.close()


# ---------------------------------------------------------------------------
# HTTP status error tests
# ---------------------------------------------------------------------------


class TestRequestStatusErrors:
    """Tests for HTTP status code error mapping in _request."""

    def test_403_raises_auth_error(self) -> None:
        """403 response raises AuthError via make_status_error."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(
            403, json_body={"type": "BadClientCredentialsError", "message": "Forbidden"}
        )
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
            assert False, "Expected AuthError"
        except AuthError as exc:
            assert exc.status_code == 403
        finally:
            client.close()

    def test_404_raises_not_found_error(self) -> None:
        """404 response raises NotFoundError via make_status_error."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(
            404, json_body={"type": "EntityNotFoundError", "message": "Not found"}
        )
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
            assert False, "Expected NotFoundError"
        except NotFoundError as exc:
            assert exc.status_code == 404
        finally:
            client.close()

    def test_500_raises_server_error(self) -> None:
        """500 response raises ServerError via make_status_error."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(
            500,
            json_body={"type": "ServerUnexpectedFailure", "message": "Internal error"},
        )
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
            assert False, "Expected ServerError"
        except ServerError as exc:
            assert exc.status_code == 500
        finally:
            client.close()


# ---------------------------------------------------------------------------
# 429 retry tests
# ---------------------------------------------------------------------------


class TestRequest429Retry:
    """Tests for 429 rate limit retry with exponential backoff."""

    @patch("sonnys_data_client._client.time.sleep")
    def test_429_retry_success(self, mock_sleep) -> None:
        """First call returns 429, second returns 200 -- _request succeeds."""
        client = SonnysClient("id", "key")
        response_429 = _make_response(
            429, json_body={"type": "RequestRateExceedError", "message": "Rate exceeded"}
        )
        response_200 = _make_response(200, json_body={"data": "ok"})
        client._session.request = MagicMock(
            side_effect=[response_429, response_200]
        )
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        result = client._request("GET", "/test")

        assert result is response_200
        assert result.status_code == 200
        # Should have been called twice (initial + 1 retry)
        assert client._session.request.call_count == 2
        client.close()

    @patch("sonnys_data_client._client.time.sleep")
    def test_429_retry_exhausted_raises_rate_limit_error(self, mock_sleep) -> None:
        """All calls return 429 -- raises RateLimitError after max_retries."""
        client = SonnysClient("id", "key", max_retries=3)
        response_429 = _make_response(
            429, json_body={"type": "RequestRateExceedError", "message": "Rate exceeded"}
        )
        client._session.request = MagicMock(return_value=response_429)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
            assert False, "Expected RateLimitError"
        except RateLimitError as exc:
            assert exc.status_code == 429
        finally:
            client.close()

        # 1 initial + 3 retries = 4 total calls
        assert client._session.request.call_count == 4

    @patch("sonnys_data_client._client.time.sleep")
    def test_429_backoff_timing(self, mock_sleep) -> None:
        """Verify exponential backoff sleep calls: 1s, 2s, 4s."""
        client = SonnysClient("id", "key", max_retries=3)
        response_429 = _make_response(
            429, json_body={"type": "RequestRateExceedError", "message": "Rate exceeded"}
        )
        client._session.request = MagicMock(return_value=response_429)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        try:
            client._request("GET", "/test")
        except RateLimitError:
            pass
        finally:
            client.close()

        # Backoff sleeps: attempt 0 -> 1s, attempt 1 -> 2s, attempt 2 -> 4s
        # (only after 429, not after the final attempt that raises)
        backoff_calls = [c for c in mock_sleep.call_args_list if c != call(0.0)]
        # Filter out rate limiter sleeps (0.0) -- only backoff sleeps remain
        assert call(1.0) in mock_sleep.call_args_list
        assert call(2.0) in mock_sleep.call_args_list
        assert call(4.0) in mock_sleep.call_args_list


# ---------------------------------------------------------------------------
# Rate limiter integration tests
# ---------------------------------------------------------------------------


class TestRequestRateLimiter:
    """Tests for rate limiter integration in _request."""

    def test_acquire_called_before_each_request(self) -> None:
        """rate_limiter.acquire() is called before each HTTP request."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(200, json_body={"data": "ok"})
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.0)

        client._request("GET", "/test")

        client._rate_limiter.acquire.assert_called_once()
        client.close()

    @patch("sonnys_data_client._client.time.sleep")
    def test_rate_limiter_wait_triggers_sleep(self, mock_sleep) -> None:
        """When acquire() returns > 0, sleep is called with that value."""
        client = SonnysClient("id", "key")
        mock_response = _make_response(200, json_body={"data": "ok"})
        client._session.request = MagicMock(return_value=mock_response)
        client._rate_limiter.acquire = MagicMock(return_value=0.5)

        client._request("GET", "/test")

        mock_sleep.assert_called_with(0.5)
        client.close()
