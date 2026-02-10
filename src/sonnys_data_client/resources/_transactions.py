"""Transactions resource."""

from __future__ import annotations

from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._base import SonnysModel
from sonnys_data_client.types._transactions import (
    Transaction,
    TransactionListItem,
    TransactionV2ListItem,
)


class Transactions(ListableResource, GettableResource):
    """Access the /transaction list, detail, and by-type endpoints."""

    _path = "/transaction"
    _items_key = "transactions"
    _model = TransactionListItem
    _default_limit = 100
    _paginated = True

    _detail_path = "/transaction/{id}"
    _detail_model = Transaction

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
            total = data["total"]

            for item in items:
                all_items.append(model.model_validate(item))

            offset += limit
            if offset > total:
                break

        return all_items

    def list_by_type(self, item_type: str, **params: object) -> list[TransactionListItem]:
        """Fetch all transactions of a specific type.

        Valid types include: wash, prepaid-wash, recurring, washbook,
        giftcard, merchandise, house-account. The API validates the type
        parameter.

        Args:
            item_type: The transaction type to filter by.
            **params: Extra query parameters forwarded to every request
                (e.g., ``startDate``, ``endDate``, ``site``, ``region``).

        Returns:
            A flat list of :class:`TransactionListItem` instances.
        """
        return self._paginated_fetch(
            f"/transaction/type/{item_type}",
            "transactions",
            TransactionListItem,
            **params,
        )

    def list_v2(self, **params: object) -> list[TransactionV2ListItem]:
        """Fetch all transactions using the v2 endpoint.

        The v2 endpoint returns enriched list items with ``customer_id``,
        ``is_recurring_plan_sale``, ``is_recurring_plan_redemption``, and
        ``transaction_status`` fields.

        Note: The API caches v2 responses for 10 minutes per reporting criteria.

        Returns:
            A flat list of :class:`TransactionV2ListItem` instances.
        """
        return self._paginated_fetch(
            "/transaction/version-2",
            "transactions",
            TransactionV2ListItem,
            **params,
        )
