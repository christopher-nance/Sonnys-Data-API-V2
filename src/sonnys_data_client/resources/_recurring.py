"""Recurring accounts resource."""

from __future__ import annotations

from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._base import SonnysModel
from sonnys_data_client.types._recurring import (
    Recurring,
    RecurringListItem,
    RecurringModification,
    RecurringStatusChange,
)


class RecurringAccounts(ListableResource, GettableResource):
    """Access the /recurring/account list, detail, and custom endpoints.

    The most feature-rich resource, providing paginated account search,
    individual account lookup, and specialized reporting endpoints.

    - ``list()`` returns :class:`~sonnys_data_client.types.RecurringListItem`
      summaries with status and billing site info.
    - ``get(id)`` returns a full :class:`~sonnys_data_client.types.Recurring`
      record with billing history, tags, vehicles, and customer details.
    - ``list_status_changes()`` fetches status transition history.
    - ``list_modifications()`` fetches account modification audit logs.
    - ``list_details()`` fetches all accounts with full detail in bulk.
    """

    _path = "/recurring/account/list"
    _items_key = "accounts"
    _model = RecurringListItem
    _default_limit = 100
    _paginated = True

    _detail_path = "/recurring/account/{id}/detail"
    _detail_model = Recurring

    def _paginated_fetch(
        self,
        path: str,
        items_key: str,
        model: type[SonnysModel],
        limit: int = 100,
        **params: object,
    ) -> list[SonnysModel]:
        """Fetch all pages from a paginated endpoint.

        Generic pagination helper used by the custom list methods to avoid
        duplicating the offset-based pagination loop.

        Args:
            path: API endpoint path.
            items_key: Key inside ``data`` that holds the items array.
            model: Pydantic model class to validate each item against.
            limit: Page size for paginated requests.
            **params: Extra query parameters forwarded to every request.

        Returns:
            A list of validated Pydantic model instances.
        """
        all_items: list[SonnysModel] = []
        offset = 1

        while True:
            request_params = {
                "limit": limit,
                "offset": offset,
                **params,
            }
            response = self._client._request("GET", path, params=request_params)
            data = response.json()["data"]

            items = data[items_key]
            total = data.get("total")

            for item in items:
                all_items.append(model.model_validate(item))

            offset += limit
            if total is None or offset > total:
                break

        return all_items

    def list_status_changes(self, **params: object) -> list[RecurringStatusChange]:
        """Fetch all recurring account status changes.

        Returns:
            A flat list of :class:`RecurringStatusChange` instances.
        """
        return self._paginated_fetch(
            "/recurring/account/status-list",
            "accounts",
            RecurringStatusChange,
            **params,
        )

    def list_modifications(self, **params: object) -> list[RecurringModification]:
        """Fetch all recurring account modifications.

        Returns:
            A flat list of :class:`RecurringModification` instances.
        """
        return self._paginated_fetch(
            "/recurring/account/modifications",
            "accounts",
            RecurringModification,
            **params,
        )

    def list_details(self, **params: object) -> list[Recurring]:
        """Fetch all recurring accounts with full detail.

        Unlike :meth:`list` which returns summary :class:`RecurringListItem`
        objects, this method returns full :class:`Recurring` detail objects.

        Returns:
            A flat list of :class:`Recurring` instances.
        """
        return self._paginated_fetch(
            "/recurring/account/details/list",
            "accounts",
            Recurring,
            **params,
        )
