"""Tests for Transactions.load_job() batch job submit-poll-return flow."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from sonnys_data_client._client import SonnysClient
from sonnys_data_client._exceptions import APIError, APITimeoutError
from sonnys_data_client.resources._transactions import Transactions
from sonnys_data_client.types._transactions import TransactionJobItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(status_code: int, *, json_body: object) -> requests.models.Response:
    """Build a requests.Response for testing without making real HTTP calls."""
    resp = requests.models.Response()
    resp.status_code = status_code
    payload = json.dumps(json_body).encode("utf-8")
    resp._content = payload
    resp.headers["Content-Type"] = "application/json"
    resp.encoding = "utf-8"
    return resp


def _make_client() -> SonnysClient:
    """Create a SonnysClient with mocked internals for resource testing."""
    client = SonnysClient("id", "key")
    client._rate_limiter.acquire = MagicMock(return_value=0.0)
    return client


SAMPLE_HASH = "1aabac6d068eef6a7bad3fdf50a05cc8"

SAMPLE_JOB_ITEM = {
    "id": "txn-001",
    "number": 123,
    "type": "Sale",
    "completeDate": "2020-06-01T12:00:00Z",
    "locationCode": "MAIN",
    "salesDeviceName": "POS-1",
    "total": 15.99,
    "tenders": [
        {
            "tender": "Credit",
            "tenderSubType": None,
            "amount": 15.99,
            "change": 0.0,
            "total": 15.99,
            "referenceNumber": None,
            "creditCardLastFour": "1234",
            "creditCardExpirationDate": "12/25",
        }
    ],
    "items": [
        {
            "name": "Basic Wash",
            "sku": "WASH-001",
            "department": "Wash",
            "quantity": 1,
            "gross": 15.99,
            "net": 15.99,
            "discount": 0.0,
            "tax": 0.0,
            "additionalFee": 0.0,
            "isVoided": False,
        }
    ],
    "discounts": [],
    "isRecurringPayment": False,
    "isRecurringRedemption": False,
    "isRecurringSale": False,
    "isPrepaidRedemption": False,
    "isPrepaidSale": False,
    "customerId": "1:234",
    "isRecurringPlanSale": False,
    "isRecurringPlanRedemption": False,
    "transactionStatus": "Completed",
}


def _load_job_response() -> requests.models.Response:
    """Build a mock response for POST /transaction/load-job."""
    return _make_response(200, json_body={"data": {"hash": SAMPLE_HASH}})


def _get_job_data_response(
    status: str, data: list | None = None
) -> requests.models.Response:
    """Build a mock response for GET /transaction/get-job-data."""
    return _make_response(
        200,
        json_body={
            "data": {
                "hash": SAMPLE_HASH,
                "status": status,
                "data": data or [],
                "offset": 0,
                "limit": 100,
                "total": len(data) if data else 0,
            }
        },
    )


# ---------------------------------------------------------------------------
# Tests: Submit job and get hash
# ---------------------------------------------------------------------------


class TestLoadJobSubmit:
    """Tests for job submission (POST to /transaction/load-job)."""

    def test_submit_posts_to_load_job_endpoint(self) -> None:
        """load_job() POSTs to /transaction/load-job with provided params."""
        client = _make_client()

        submit_resp = _load_job_response()
        poll_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(side_effect=[submit_resp, poll_resp])

        resource = Transactions(client)
        with patch("sonnys_data_client.resources._transactions.time"):
            resource.load_job(startDate=1591040159, endDate=1591126559)

        # First call should be POST to /transaction/load-job
        first_call = client._request.call_args_list[0]
        assert first_call[0][0] == "POST"
        assert first_call[0][1] == "/transaction/load-job"
        assert first_call[1]["params"]["startDate"] == 1591040159
        assert first_call[1]["params"]["endDate"] == 1591126559

        client.close()

    def test_submit_extracts_hash_for_polling(self) -> None:
        """load_job() uses the hash from the submit response to poll."""
        client = _make_client()

        submit_resp = _load_job_response()
        poll_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(side_effect=[submit_resp, poll_resp])

        resource = Transactions(client)
        with patch("sonnys_data_client.resources._transactions.time"):
            resource.load_job(startDate=1591040159, endDate=1591126559)

        # Second call should be GET to /transaction/get-job-data with the hash
        second_call = client._request.call_args_list[1]
        assert second_call[0][0] == "GET"
        assert second_call[0][1] == "/transaction/get-job-data"
        assert second_call[1]["params"] == {"hash": SAMPLE_HASH}

        client.close()


# ---------------------------------------------------------------------------
# Tests: Immediate pass
# ---------------------------------------------------------------------------


class TestLoadJobImmediatePass:
    """Tests for immediate pass (status='pass' on first poll)."""

    def test_immediate_pass_returns_transaction_job_items(self) -> None:
        """When first poll returns status='pass', return parsed items immediately."""
        client = _make_client()

        submit_resp = _load_job_response()
        poll_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(side_effect=[submit_resp, poll_resp])

        resource = Transactions(client)
        with patch("sonnys_data_client.resources._transactions.time"):
            result = resource.load_job(startDate=1591040159, endDate=1591126559)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TransactionJobItem)
        # Two calls total: submit + one poll
        assert client._request.call_count == 2

        client.close()


# ---------------------------------------------------------------------------
# Tests: Working then pass
# ---------------------------------------------------------------------------


class TestLoadJobWorkingThenPass:
    """Tests for working → pass transition with sleep between polls."""

    @patch("sonnys_data_client.resources._transactions.time")
    def test_working_then_pass_sleeps_and_returns(self, mock_time: MagicMock) -> None:
        """When first poll returns 'working', sleep then poll again for 'pass'."""
        mock_time.monotonic.side_effect = [0.0, 1.0, 3.0]  # start, first poll check, second poll check
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")
        pass_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(side_effect=[submit_resp, working_resp, pass_resp])

        resource = Transactions(client)
        result = resource.load_job(
            startDate=1591040159, endDate=1591126559, timeout=300.0
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TransactionJobItem)
        # Three calls: submit + working poll + pass poll
        assert client._request.call_count == 3
        # Should have slept once with the default poll_interval
        mock_time.sleep.assert_called_once_with(2.0)

        client.close()

    @patch("sonnys_data_client.resources._transactions.time")
    def test_multiple_working_then_pass(self, mock_time: MagicMock) -> None:
        """Multiple 'working' responses before 'pass' — sleeps between each."""
        mock_time.monotonic.side_effect = [0.0, 1.0, 3.0, 5.0]  # start, check1, check2, check3
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working1 = _get_job_data_response("working")
        working2 = _get_job_data_response("working")
        pass_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(
            side_effect=[submit_resp, working1, working2, pass_resp]
        )

        resource = Transactions(client)
        result = resource.load_job(
            startDate=1591040159, endDate=1591126559, timeout=300.0
        )

        assert len(result) == 1
        assert client._request.call_count == 4
        assert mock_time.sleep.call_count == 2

        client.close()


# ---------------------------------------------------------------------------
# Tests: Job failure
# ---------------------------------------------------------------------------


class TestLoadJobFailure:
    """Tests for job failure (status='fail')."""

    def test_fail_status_raises_api_error(self) -> None:
        """When poll returns status='fail', raise APIError."""
        client = _make_client()

        submit_resp = _load_job_response()
        fail_resp = _get_job_data_response("fail")

        client._request = MagicMock(side_effect=[submit_resp, fail_resp])

        resource = Transactions(client)
        with patch("sonnys_data_client.resources._transactions.time"):
            with pytest.raises(APIError, match="Batch job failed"):
                resource.load_job(startDate=1591040159, endDate=1591126559)

        client.close()

    @patch("sonnys_data_client.resources._transactions.time")
    def test_working_then_fail(self, mock_time: MagicMock) -> None:
        """Job starts working then fails — raises APIError after working poll."""
        mock_time.monotonic.side_effect = [0.0, 1.0]  # start, first poll check
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")
        fail_resp = _get_job_data_response("fail")

        client._request = MagicMock(
            side_effect=[submit_resp, working_resp, fail_resp]
        )

        resource = Transactions(client)
        with pytest.raises(APIError, match="Batch job failed"):
            resource.load_job(
                startDate=1591040159, endDate=1591126559, timeout=300.0
            )

        assert client._request.call_count == 3

        client.close()


# ---------------------------------------------------------------------------
# Tests: Poll timeout
# ---------------------------------------------------------------------------


class TestLoadJobTimeout:
    """Tests for poll timeout (keeps returning 'working' past deadline)."""

    @patch("sonnys_data_client.resources._transactions.time")
    def test_timeout_raises_api_timeout_error(self, mock_time: MagicMock) -> None:
        """When deadline exceeded during 'working', raise APITimeoutError."""
        # monotonic: start=0, deadline=0+60=60, after poll check=61 (past deadline)
        mock_time.monotonic.side_effect = [0.0, 61.0]
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")

        client._request = MagicMock(side_effect=[submit_resp, working_resp])

        resource = Transactions(client)
        with pytest.raises(APITimeoutError, match="60"):
            resource.load_job(
                startDate=1591040159, endDate=1591126559, timeout=60.0
            )

        client.close()

    @patch("sonnys_data_client.resources._transactions.time")
    def test_timeout_after_multiple_working_polls(self, mock_time: MagicMock) -> None:
        """Timeout after several working polls — polls until deadline exceeded."""
        # monotonic: start=0, check1=10 (<60), check2=61 (>=60)
        mock_time.monotonic.side_effect = [0.0, 10.0, 61.0]
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working1 = _get_job_data_response("working")
        working2 = _get_job_data_response("working")

        client._request = MagicMock(
            side_effect=[submit_resp, working1, working2]
        )

        resource = Transactions(client)
        with pytest.raises(APITimeoutError):
            resource.load_job(
                startDate=1591040159, endDate=1591126559, timeout=60.0
            )

        # submit + 2 working polls
        assert client._request.call_count == 3
        # slept once (after first working, before second working which triggers timeout)
        assert mock_time.sleep.call_count == 1

        client.close()


# ---------------------------------------------------------------------------
# Tests: Data parsing
# ---------------------------------------------------------------------------


class TestLoadJobDataParsing:
    """Tests for TransactionJobItem parsing from response data."""

    def test_items_parsed_as_transaction_job_item(self) -> None:
        """Each item in response data is parsed through TransactionJobItem.model_validate."""
        client = _make_client()

        second_item = {
            **SAMPLE_JOB_ITEM,
            "id": "txn-002",
            "number": 456,
            "total": 29.99,
            "customerId": "1:567",
            "transactionStatus": "Voided",
        }
        submit_resp = _load_job_response()
        poll_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM, second_item])

        client._request = MagicMock(side_effect=[submit_resp, poll_resp])

        resource = Transactions(client)
        with patch("sonnys_data_client.resources._transactions.time"):
            result = resource.load_job(startDate=1591040159, endDate=1591126559)

        assert len(result) == 2
        assert all(isinstance(item, TransactionJobItem) for item in result)

        # Verify first item fields parsed correctly
        assert result[0].id == "txn-001"
        assert result[0].number == 123
        assert result[0].total == 15.99
        assert result[0].customer_id == "1:234"
        assert result[0].transaction_status == "Completed"
        assert result[0].is_recurring_plan_sale is False

        # Verify second item
        assert result[1].id == "txn-002"
        assert result[1].number == 456
        assert result[1].total == 29.99
        assert result[1].customer_id == "1:567"
        assert result[1].transaction_status == "Voided"

        client.close()

    def test_empty_data_returns_empty_list(self) -> None:
        """When status='pass' but data is empty, return empty list."""
        client = _make_client()

        submit_resp = _load_job_response()
        poll_resp = _get_job_data_response("pass", [])

        client._request = MagicMock(side_effect=[submit_resp, poll_resp])

        resource = Transactions(client)
        with patch("sonnys_data_client.resources._transactions.time"):
            result = resource.load_job(startDate=1591040159, endDate=1591126559)

        assert result == []

        client.close()


# ---------------------------------------------------------------------------
# Tests: Configurable poll_interval and timeout
# ---------------------------------------------------------------------------


class TestLoadJobConfiguration:
    """Tests for configurable poll_interval and timeout parameters."""

    @patch("sonnys_data_client.resources._transactions.time")
    def test_custom_poll_interval(self, mock_time: MagicMock) -> None:
        """Custom poll_interval is used for time.sleep between polls."""
        mock_time.monotonic.side_effect = [0.0, 1.0]  # start, first check
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")
        pass_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(
            side_effect=[submit_resp, working_resp, pass_resp]
        )

        resource = Transactions(client)
        resource.load_job(
            startDate=1591040159,
            endDate=1591126559,
            poll_interval=5.0,
            timeout=300.0,
        )

        mock_time.sleep.assert_called_once_with(5.0)

        client.close()

    @patch("sonnys_data_client.resources._transactions.time")
    def test_custom_timeout_used_for_deadline(self, mock_time: MagicMock) -> None:
        """Custom timeout value is used in the deadline calculation."""
        # monotonic: start=0, deadline=0+10=10, after poll check=11 (past deadline)
        mock_time.monotonic.side_effect = [0.0, 11.0]
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")

        client._request = MagicMock(side_effect=[submit_resp, working_resp])

        resource = Transactions(client)
        with pytest.raises(APITimeoutError, match="10"):
            resource.load_job(
                startDate=1591040159,
                endDate=1591126559,
                poll_interval=1.0,
                timeout=10.0,
            )

        client.close()

    @patch("sonnys_data_client.resources._transactions.time")
    def test_default_poll_interval_is_2_seconds(self, mock_time: MagicMock) -> None:
        """Default poll_interval is 2.0 seconds."""
        mock_time.monotonic.side_effect = [0.0, 1.0]
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")
        pass_resp = _get_job_data_response("pass", [SAMPLE_JOB_ITEM])

        client._request = MagicMock(
            side_effect=[submit_resp, working_resp, pass_resp]
        )

        resource = Transactions(client)
        resource.load_job(startDate=1591040159, endDate=1591126559)

        mock_time.sleep.assert_called_once_with(2.0)

        client.close()

    @patch("sonnys_data_client.resources._transactions.time")
    def test_default_timeout_is_300_seconds(self, mock_time: MagicMock) -> None:
        """Default timeout is 300.0 seconds (5 minutes)."""
        # At 301s, should timeout with default 300s timeout
        mock_time.monotonic.side_effect = [0.0, 301.0]
        mock_time.sleep = MagicMock()

        client = _make_client()

        submit_resp = _load_job_response()
        working_resp = _get_job_data_response("working")

        client._request = MagicMock(side_effect=[submit_resp, working_resp])

        resource = Transactions(client)
        with pytest.raises(APITimeoutError, match="300"):
            resource.load_job(startDate=1591040159, endDate=1591126559)

        client.close()
