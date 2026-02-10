"""Tests for base resource classes with auto-pagination and detail retrieval."""

import json
from unittest.mock import MagicMock, call

import requests

from sonnys_data_client._client import SonnysClient
from sonnys_data_client._resources import BaseResource, ListableResource, GettableResource
from sonnys_data_client.types._base import SonnysModel


# ---------------------------------------------------------------------------
# Test-only Pydantic models
# ---------------------------------------------------------------------------


class DummyListItem(SonnysModel):
    """Minimal model for list endpoint tests."""

    item_id: int
    name: str


class DummyDetail(SonnysModel):
    """Minimal model for detail endpoint tests."""

    item_id: int
    name: str
    description: str


# ---------------------------------------------------------------------------
# Test-only concrete resource subclasses
# ---------------------------------------------------------------------------


class PaginatedResource(ListableResource):
    """Paginated list resource for testing."""

    _path = "/customer"
    _items_key = "customers"
    _model = DummyListItem
    _default_limit = 100
    _paginated = True


class NonPaginatedResource(ListableResource):
    """Non-paginated list resource for testing (e.g., sites)."""

    _path = "/site"
    _items_key = "sites"
    _model = DummyListItem
    _paginated = False


class DetailResource(GettableResource):
    """Detail resource for testing."""

    _detail_path = "/customer/{id}"
    _detail_model = DummyDetail


class ComplexPathResource(GettableResource):
    """Detail resource with complex path for testing."""

    _detail_path = "/washbook/account/{id}/detail"
    _detail_model = DummyDetail


class FullResource(ListableResource, GettableResource):
    """Resource with both list and detail for testing."""

    _path = "/customer"
    _items_key = "customers"
    _model = DummyListItem
    _default_limit = 100
    _paginated = True
    _detail_path = "/customer/{id}"
    _detail_model = DummyDetail


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


# ---------------------------------------------------------------------------
# Auto-paginated list tests
# ---------------------------------------------------------------------------


class TestListAutoPaginated:
    """Tests for ListableResource.list() with pagination."""

    def test_multi_page_aggregation(self) -> None:
        """list() aggregates items across 3 pages (100+100+50 = 250 total)."""
        client = _make_client()

        # Page 1: offset=1, 100 items
        page1_items = [{"itemId": i, "name": f"Item {i}"} for i in range(1, 101)]
        resp1 = _make_response(200, json_body={
            "data": {"customers": page1_items, "offset": 1, "limit": 100, "total": 250}
        })

        # Page 2: offset=101, 100 items
        page2_items = [{"itemId": i, "name": f"Item {i}"} for i in range(101, 201)]
        resp2 = _make_response(200, json_body={
            "data": {"customers": page2_items, "offset": 101, "limit": 100, "total": 250}
        })

        # Page 3: offset=201, 50 items
        page3_items = [{"itemId": i, "name": f"Item {i}"} for i in range(201, 251)]
        resp3 = _make_response(200, json_body={
            "data": {"customers": page3_items, "offset": 201, "limit": 100, "total": 250}
        })

        client._request = MagicMock(side_effect=[resp1, resp2, resp3])

        resource = PaginatedResource(client)
        results = resource.list()

        # Should return all 250 items as DummyListItem instances
        assert len(results) == 250
        assert all(isinstance(item, DummyListItem) for item in results)
        assert results[0].item_id == 1
        assert results[0].name == "Item 1"
        assert results[249].item_id == 250
        assert results[249].name == "Item 250"

        # Should have made 3 requests with correct offsets
        assert client._request.call_count == 3
        client._request.assert_any_call(
            "GET", "/customer", params={"limit": 100, "offset": 1}
        )
        client._request.assert_any_call(
            "GET", "/customer", params={"limit": 100, "offset": 101}
        )
        client._request.assert_any_call(
            "GET", "/customer", params={"limit": 100, "offset": 201}
        )

        client.close()

    def test_single_page(self) -> None:
        """list() returns all items from one request when total <= limit."""
        client = _make_client()

        items = [{"itemId": i, "name": f"Item {i}"} for i in range(1, 51)]
        resp = _make_response(200, json_body={
            "data": {"customers": items, "offset": 1, "limit": 100, "total": 50}
        })

        client._request = MagicMock(return_value=resp)

        resource = PaginatedResource(client)
        results = resource.list()

        assert len(results) == 50
        assert all(isinstance(item, DummyListItem) for item in results)
        assert client._request.call_count == 1
        client._request.assert_called_once_with(
            "GET", "/customer", params={"limit": 100, "offset": 1}
        )

        client.close()

    def test_empty_list(self) -> None:
        """list() returns empty list when total=0."""
        client = _make_client()

        resp = _make_response(200, json_body={
            "data": {"customers": [], "offset": 0, "limit": 100, "total": 0}
        })

        client._request = MagicMock(return_value=resp)

        resource = PaginatedResource(client)
        results = resource.list()

        assert results == []
        assert client._request.call_count == 1

        client.close()

    def test_extra_params_forwarded(self) -> None:
        """list() forwards extra keyword params alongside offset/limit."""
        client = _make_client()

        items = [{"itemId": 1, "name": "John Doe"}]
        resp = _make_response(200, json_body={
            "data": {"customers": items, "offset": 1, "limit": 100, "total": 1}
        })

        client._request = MagicMock(return_value=resp)

        resource = PaginatedResource(client)
        results = resource.list(first_name="John", status="active")

        assert len(results) == 1
        client._request.assert_called_once_with(
            "GET", "/customer", params={
                "limit": 100,
                "offset": 1,
                "first_name": "John",
                "status": "active",
            }
        )

        client.close()


# ---------------------------------------------------------------------------
# Non-paginated list tests
# ---------------------------------------------------------------------------


class TestListNonPaginated:
    """Tests for ListableResource.list() with _paginated=False."""

    def test_non_paginated_single_request(self) -> None:
        """Non-paginated list makes one request without offset/limit."""
        client = _make_client()

        items = [
            {"itemId": 1, "name": "Site A"},
            {"itemId": 2, "name": "Site B"},
            {"itemId": 3, "name": "Site C"},
        ]
        resp = _make_response(200, json_body={
            "data": {"sites": items}
        })

        client._request = MagicMock(return_value=resp)

        resource = NonPaginatedResource(client)
        results = resource.list()

        assert len(results) == 3
        assert all(isinstance(item, DummyListItem) for item in results)
        assert results[0].item_id == 1
        assert results[0].name == "Site A"
        assert results[2].item_id == 3
        assert results[2].name == "Site C"

        # Should make exactly one request with NO offset/limit params
        assert client._request.call_count == 1
        client._request.assert_called_once_with(
            "GET", "/site", params={}
        )

        client.close()

    def test_non_paginated_with_extra_params(self) -> None:
        """Non-paginated list forwards extra params without offset/limit."""
        client = _make_client()

        items = [{"itemId": 1, "name": "Site A"}]
        resp = _make_response(200, json_body={
            "data": {"sites": items}
        })

        client._request = MagicMock(return_value=resp)

        resource = NonPaginatedResource(client)
        results = resource.list(region="east")

        assert len(results) == 1
        client._request.assert_called_once_with(
            "GET", "/site", params={"region": "east"}
        )

        client.close()


# ---------------------------------------------------------------------------
# Detail get tests
# ---------------------------------------------------------------------------


class TestDetailGet:
    """Tests for GettableResource.get() method."""

    def test_get_parses_detail_envelope(self) -> None:
        """get() calls correct path and parses data envelope into model."""
        client = _make_client()

        resp = _make_response(200, json_body={
            "data": {"itemId": 12345, "name": "Test Customer", "description": "VIP"}
        })

        client._request = MagicMock(return_value=resp)

        resource = DetailResource(client)
        result = resource.get("12345")

        assert isinstance(result, DummyDetail)
        assert result.item_id == 12345
        assert result.name == "Test Customer"
        assert result.description == "VIP"

        client._request.assert_called_once_with("GET", "/customer/12345")

        client.close()

    def test_get_complex_path(self) -> None:
        """get() handles complex path with {id} in the middle."""
        client = _make_client()

        resp = _make_response(200, json_body={
            "data": {"itemId": 999, "name": "Account Detail", "description": "Full"}
        })

        client._request = MagicMock(return_value=resp)

        resource = ComplexPathResource(client)
        result = resource.get("999")

        assert isinstance(result, DummyDetail)
        assert result.item_id == 999

        client._request.assert_called_once_with(
            "GET", "/washbook/account/999/detail"
        )

        client.close()


# ---------------------------------------------------------------------------
# Combined resource tests
# ---------------------------------------------------------------------------


class TestCombinedResource:
    """Tests for resource with both list and detail capabilities."""

    def test_full_resource_can_list_and_get(self) -> None:
        """A resource inheriting both ListableResource and GettableResource works."""
        client = _make_client()

        # Test list
        list_resp = _make_response(200, json_body={
            "data": {"customers": [{"itemId": 1, "name": "A"}], "offset": 1, "limit": 100, "total": 1}
        })
        client._request = MagicMock(return_value=list_resp)

        resource = FullResource(client)
        results = resource.list()
        assert len(results) == 1
        assert isinstance(results[0], DummyListItem)

        # Test get
        detail_resp = _make_response(200, json_body={
            "data": {"itemId": 1, "name": "A", "description": "Detail"}
        })
        client._request = MagicMock(return_value=detail_resp)

        detail = resource.get("1")
        assert isinstance(detail, DummyDetail)
        assert detail.item_id == 1

        client.close()
