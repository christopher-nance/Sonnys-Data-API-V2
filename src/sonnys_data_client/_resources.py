"""Base resource classes with auto-pagination and detail retrieval."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sonnys_data_client.types._base import SonnysModel

if TYPE_CHECKING:
    from sonnys_data_client._client import SonnysClient


class BaseResource:
    """Base class for all API resources.

    Stores a reference to the parent :class:`SonnysClient` so that
    subclasses can issue HTTP requests via ``self._client._request()``.
    """

    def __init__(self, client: SonnysClient) -> None:
        self._client = client


class ListableResource(BaseResource):
    """Mixin for resources that support a paginated (or non-paginated) list endpoint.

    Subclasses must define the following class attributes:

    - ``_path``: URL path for the list endpoint (e.g., ``"/customer"``).
    - ``_items_key``: Key inside ``data`` that holds the items array
      (e.g., ``"customers"``).
    - ``_model``: Pydantic model class to validate each item against.
    - ``_default_limit``: Page size for paginated requests (default ``100``).
    - ``_paginated``: Whether the endpoint supports offset/limit pagination
      (default ``True``).  Set to ``False`` for endpoints like ``/site`` that
      return all records in a single response.
    """

    _path: str
    _items_key: str
    _model: type[SonnysModel]
    _default_limit: int = 100
    _paginated: bool = True

    def list(self, **params: object) -> list[SonnysModel]:
        """Fetch all items from the list endpoint.

        For paginated endpoints, automatically pages through all results
        using offset-based pagination (offset starts at 1 per API spec).

        For non-paginated endpoints (``_paginated=False``), makes a single
        request and returns all items.

        Args:
            **params: Extra query parameters forwarded to every request
                (e.g., ``first_name="John"``).

        Returns:
            A list of validated Pydantic model instances.
        """
        if not self._paginated:
            return self._list_non_paginated(**params)
        return self._list_paginated(**params)

    def _list_paginated(self, **params: object) -> list[SonnysModel]:
        """Fetch all pages from a paginated list endpoint."""
        all_items: list[SonnysModel] = []
        offset = 1

        while True:
            request_params = {
                "limit": self._default_limit,
                "offset": offset,
                **params,
            }
            response = self._client._request("GET", self._path, params=request_params)
            data = response.json()["data"]

            items = data[self._items_key]
            total = data.get("total")

            for item in items:
                all_items.append(self._model.model_validate(item))

            offset += self._default_limit
            if total is None or offset > total:
                break

        return all_items

    def _list_non_paginated(self, **params: object) -> list[SonnysModel]:
        """Fetch all items from a non-paginated list endpoint."""
        response = self._client._request("GET", self._path, params={**params})
        data = response.json()["data"]
        items = data[self._items_key]
        return [self._model.model_validate(item) for item in items]


class GettableResource(BaseResource):
    """Mixin for resources that support a detail (get-by-ID) endpoint.

    Subclasses must define the following class attributes:

    - ``_detail_path``: URL path template with ``{id}`` placeholder
      (e.g., ``"/customer/{id}"``).
    - ``_detail_model``: Pydantic model class to validate the detail
      response against.
    """

    _detail_path: str
    _detail_model: type[SonnysModel]

    def get(self, id: str) -> SonnysModel:
        """Fetch a single resource by its ID.

        Args:
            id: The resource identifier, substituted into ``_detail_path``.

        Returns:
            A validated Pydantic model instance.
        """
        path = self._detail_path.replace("{id}", id)
        response = self._client._request("GET", path)
        data = response.json()["data"]
        return self._detail_model.model_validate(data)
