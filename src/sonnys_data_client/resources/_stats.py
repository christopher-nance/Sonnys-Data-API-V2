"""Stats resource for business analytics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sonnys_data_client._date_utils import parse_date_range
from sonnys_data_client._resources import BaseResource
from sonnys_data_client.types._transactions import (
    TransactionListItem,
    TransactionV2ListItem,
)

if TYPE_CHECKING:
    from sonnys_data_client._client import SonnysClient


class StatsResource(BaseResource):
    """Access computed business analytics and KPIs.

    Unlike other resources that wrap REST endpoints directly,
    ``StatsResource`` computes analytics by fetching raw data and
    aggregating it locally.  Individual stat methods (total sales,
    total washes, conversion rate, etc.) will be added in Phases 21-25.

    All stat methods accept a date range and delegate to
    :meth:`_resolve_dates` for consistent parsing and validation.
    """

    def __init__(self, client: SonnysClient) -> None:
        super().__init__(client)

    def _resolve_dates(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> dict[str, int]:
        """Validate a date range and convert to Unix timestamp parameters.

        Delegates to :func:`~sonnys_data_client._date_utils.parse_date_range`
        for parsing and validation, then converts the resulting datetimes to
        integer Unix timestamps suitable for API query parameters.

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A dict with ``startDate`` and ``endDate`` keys whose values are
            Unix timestamps (int), ready to pass as query parameters.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.
        """
        start_dt, end_dt = parse_date_range(start, end)
        return {
            "startDate": int(start_dt.timestamp()),
            "endDate": int(end_dt.timestamp()),
        }

    def _fetch_transactions(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> list[TransactionListItem]:
        """Fetch all transactions within a date range.

        Delegates to :meth:`~sonnys_data_client.resources.Transactions.list`
        after converting the date range to Unix timestamp query parameters.

        Used by stat methods that need the full transaction list (e.g.
        total sales as the sum of transaction totals).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A list of :class:`TransactionListItem` instances for the range.
        """
        return self._client.transactions.list(**self._resolve_dates(start, end))

    def _fetch_transactions_by_type(
        self,
        start: str | datetime,
        end: str | datetime,
        item_type: str,
    ) -> list[TransactionListItem]:
        """Fetch all transactions of a specific type within a date range.

        Delegates to
        :meth:`~sonnys_data_client.resources.Transactions.list_by_type`
        after converting the date range to Unix timestamp query parameters.

        Used by stat methods that need type-filtered transactions (e.g.
        total washes, retail wash count).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.
            item_type: The transaction type to filter by (e.g. ``"wash"``,
                ``"recurring"``, ``"prepaid-wash"``).

        Returns:
            A list of :class:`TransactionListItem` instances matching the
            given type within the range.
        """
        return self._client.transactions.list_by_type(
            item_type, **self._resolve_dates(start, end)
        )

    def _fetch_transactions_v2(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> list[TransactionV2ListItem]:
        """Fetch all transactions using the enriched v2 endpoint.

        Delegates to
        :meth:`~sonnys_data_client.resources.Transactions.list_v2`
        after converting the date range to Unix timestamp query parameters.

        The v2 endpoint returns enriched records with
        ``is_recurring_plan_sale``, ``is_recurring_plan_redemption``, and
        ``transaction_status`` fields, enabling single-fetch efficiency for
        stat methods that need to classify transactions by multiple criteria
        (e.g. the full report method).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A list of :class:`TransactionV2ListItem` instances for the range.
        """
        return self._client.transactions.list_v2(**self._resolve_dates(start, end))
