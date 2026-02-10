"""Transactions resource."""

from __future__ import annotations

import time

from sonnys_data_client._exceptions import APIError, APITimeoutError
from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._base import SonnysModel
from sonnys_data_client.types._transactions import (
    Transaction,
    TransactionJobItem,
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
            total = data.get("total")

            for item in items:
                all_items.append(model.model_validate(item))

            offset += limit
            if total is None or offset > total:
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

    def load_job(
        self,
        *,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        **params: object,
    ) -> list[TransactionJobItem]:
        """Submit a batch job and poll until results are ready.

        Posts reporting criteria to ``/transaction/load-job``, then polls
        ``/transaction/get-job-data`` until the job completes, fails, or
        the timeout is exceeded.

        Note: The API caches job data for 20 minutes and limits the date
        range to a maximum of 24 hours.

        Args:
            poll_interval: Seconds between poll attempts (default 2.0).
            timeout: Max seconds to wait for job completion (default 300.0).
            **params: Query parameters (``startDate``, ``endDate``,
                ``site``, ``limit``, ``offset``, etc.).

        Returns:
            A list of :class:`TransactionJobItem` instances.

        Raises:
            APIError: If the job status is ``"fail"``.
            APITimeoutError: If the job does not complete within *timeout*.
        """
        # Step 1: Submit job
        response = self._client._request(
            "POST", "/transaction/load-job", params=params,
        )
        hash_value = response.json()["data"]["hash"]

        # Step 2: Poll until complete
        deadline = time.monotonic() + timeout
        while True:
            response = self._client._request(
                "GET", "/transaction/get-job-data", params={"hash": hash_value},
            )
            body = response.json()["data"]
            status = body["status"]

            if status == "pass":
                return [
                    TransactionJobItem.model_validate(item)
                    for item in body["data"]
                ]

            if status == "fail":
                raise APIError("Batch job failed")

            # status == "working"
            if time.monotonic() >= deadline:
                raise APITimeoutError(
                    f"Batch job did not complete within {timeout}s"
                )

            time.sleep(poll_interval)
