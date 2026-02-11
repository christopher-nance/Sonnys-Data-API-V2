"""Stats resource for business analytics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sonnys_data_client._date_utils import parse_date_range
from sonnys_data_client._resources import BaseResource
from sonnys_data_client.types._recurring import RecurringStatusChange
from sonnys_data_client.types._stats import ConversionResult, SalesResult, StatsReport, WashResult
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

    def _fetch_recurring_status_changes(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> list[RecurringStatusChange]:
        """Fetch recurring account status change events within a date range.

        Delegates to
        :meth:`~sonnys_data_client.resources.RecurringAccounts.list_status_changes`
        after converting the date range to Unix timestamp query parameters.

        Each status change records a transition from ``old_status`` to
        ``new_status`` along with the date, employee, and site where the
        change occurred.  Used by stat methods that analyse membership
        activity (e.g. new memberships sold by filtering for activation
        transitions).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A list of :class:`RecurringStatusChange` instances for the range.
        """
        return self._client.recurring.list_status_changes(
            **self._resolve_dates(start, end)
        )

    def retail_wash_count(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> int:
        """Count retail wash transactions for a date range.

        Fetches transactions of type ``"wash"`` and returns the count.
        Retail washes are standard single-use wash transactions (excludes
        prepaid wash book redemptions).  This value serves as the
        denominator for conversion rate calculations (Phase 24).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            The number of retail wash transactions in the date range.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.

        Example::

            count = client.stats.retail_wash_count("2026-01-01", "2026-01-31")
            print(f"Retail washes: {count}")
        """
        transactions = self._fetch_transactions_by_type(start, end, "wash")
        return len(transactions)

    def new_memberships_sold(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> int:
        """Count new membership activations for a date range.

        Fetches recurring account status changes and counts transitions
        where ``new_status`` is ``"Active"``.  This includes both brand-new
        sign-ups and reactivations of previously cancelled or suspended
        memberships.  The returned count serves as the numerator for
        conversion rate calculations (Phase 24).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            The number of membership activations in the date range.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.

        Example::

            count = client.stats.new_memberships_sold("2026-01-01", "2026-01-31")
            print(f"New memberships sold: {count}")
        """
        changes = self._fetch_recurring_status_changes(start, end)
        activations = [c for c in changes if c.new_status == "Active"]
        return len(activations)

    def total_sales(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> SalesResult:
        """Compute revenue breakdown for a date range.

        Fetches all transactions via the enriched v2 endpoint and
        categorizes them into three buckets: recurring plan sales,
        recurring redemptions, and retail.  Returns a
        :class:`~sonnys_data_client.types.SalesResult` with grand totals
        and per-bucket revenue and count.

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A :class:`~sonnys_data_client.types.SalesResult` containing
            the grand total, transaction count, and per-category
            breakdowns.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.

        Example::

            result = client.stats.total_sales("2026-01-01", "2026-01-31")
            print(f"Total: ${result.total:.2f}")
            print(f"Memberships: ${result.recurring_plan_sales:.2f}")
        """
        transactions = self._fetch_transactions_v2(start, end)

        recurring_plan_sales = 0.0
        recurring_plan_sales_count = 0
        recurring_redemptions = 0.0
        recurring_redemptions_count = 0
        retail = 0.0
        retail_count = 0

        for txn in transactions:
            if txn.is_recurring_plan_sale:
                recurring_plan_sales += txn.total
                recurring_plan_sales_count += 1
            elif txn.is_recurring_plan_redemption:
                recurring_redemptions += txn.total
                recurring_redemptions_count += 1
            else:
                retail += txn.total
                retail_count += 1

        total = recurring_plan_sales + recurring_redemptions + retail
        count = recurring_plan_sales_count + recurring_redemptions_count + retail_count

        return SalesResult(
            total=total,
            count=count,
            recurring_plan_sales=recurring_plan_sales,
            recurring_plan_sales_count=recurring_plan_sales_count,
            recurring_redemptions=recurring_redemptions,
            recurring_redemptions_count=recurring_redemptions_count,
            retail=retail,
            retail_count=retail_count,
        )

    def total_washes(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> WashResult:
        """Compute wash volume breakdown for a date range.

        Fetches transactions of type ``"wash"`` (retail) and
        ``"prepaid-wash"`` (wash book redemptions) separately and returns
        a :class:`~sonnys_data_client.types.WashResult` with per-category
        counts and a combined total.

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A :class:`~sonnys_data_client.types.WashResult` containing the
            total wash count and per-category breakdowns.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.

        Example::

            result = client.stats.total_washes("2026-01-01", "2026-01-31")
            print(f"Total washes: {result.total}")
            print(f"Retail: {result.wash_count}, Prepaid: {result.prepaid_wash_count}")
        """
        wash_transactions = self._fetch_transactions_by_type(start, end, "wash")
        prepaid_transactions = self._fetch_transactions_by_type(start, end, "prepaid-wash")

        wash_count = len(wash_transactions)
        prepaid_wash_count = len(prepaid_transactions)

        return WashResult(
            total=wash_count + prepaid_wash_count,
            wash_count=wash_count,
            prepaid_wash_count=prepaid_wash_count,
        )

    def conversion_rate(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> ConversionResult:
        """Compute the membership conversion rate for a date range.

        Measures how effectively a site converts retail wash customers
        into membership sign-ups.  The rate is computed as
        ``new_memberships / total_opportunities`` where total
        opportunities is the sum of new membership activations and
        retail wash transactions.

        Composes :meth:`new_memberships_sold` (numerator) and
        :meth:`retail_wash_count` (denominator component) into a single
        KPI.  When there are zero opportunities the rate is ``0.0``
        (division-by-zero safe).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A :class:`~sonnys_data_client.types.ConversionResult` containing
            the conversion rate, component counts, and total opportunities.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.

        Example::

            result = client.stats.conversion_rate("2026-01-01", "2026-01-31")
            print(f"Conversion rate: {result.rate:.1%}")
            print(f"Memberships: {result.new_memberships}")
            print(f"Retail washes: {result.retail_washes}")
        """
        new_memberships = self.new_memberships_sold(start, end)
        retail_washes = self.retail_wash_count(start, end)
        total_opportunities = new_memberships + retail_washes
        rate = new_memberships / total_opportunities if total_opportunities > 0 else 0.0

        return ConversionResult(
            rate=rate,
            new_memberships=new_memberships,
            retail_washes=retail_washes,
            total_opportunities=total_opportunities,
        )

    def report(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> StatsReport:
        """Compute all KPIs for a date range in a single call.

        Fetches raw data with **4 API calls** and computes every KPI
        locally, compared to the **7 API calls** that would result from
        calling :meth:`total_sales`, :meth:`total_washes`,
        :meth:`new_memberships_sold`, and :meth:`conversion_rate`
        individually.  The savings come from reusing the ``"wash"``
        transaction fetch (shared by wash count and conversion rate) and
        the recurring status-change fetch (shared by new-memberships
        and conversion rate).

        Args:
            start: Range start as an ISO-8601 string (e.g. ``"2026-01-01"``)
                or :class:`~datetime.datetime`.
            end: Range end as an ISO-8601 string or
                :class:`~datetime.datetime`.

        Returns:
            A :class:`~sonnys_data_client.types.StatsReport` containing
            ``sales``, ``washes``, ``new_memberships``, ``conversion``,
            ``period_start``, and ``period_end``.

        Raises:
            ValueError: If *start* is after *end*, or if a string cannot
                be parsed as a valid ISO-8601 date/datetime.

        Example::

            rpt = client.stats.report("2026-01-01", "2026-01-31")
            print(f"Revenue: ${rpt.sales.total:.2f}")
            print(f"Washes: {rpt.washes.total}")
            print(f"New members: {rpt.new_memberships}")
            print(f"Conversion: {rpt.conversion.rate:.1%}")
        """
        # --- 1. Fetch data (4 API calls) ---
        v2_transactions = self._fetch_transactions_v2(start, end)
        wash_transactions = self._fetch_transactions_by_type(start, end, "wash")
        prepaid_transactions = self._fetch_transactions_by_type(start, end, "prepaid-wash")
        status_changes = self._fetch_recurring_status_changes(start, end)

        # --- 2. Compute SalesResult from v2 transactions ---
        recurring_plan_sales = 0.0
        recurring_plan_sales_count = 0
        recurring_redemptions = 0.0
        recurring_redemptions_count = 0
        retail = 0.0
        retail_count = 0

        for txn in v2_transactions:
            if txn.is_recurring_plan_sale:
                recurring_plan_sales += txn.total
                recurring_plan_sales_count += 1
            elif txn.is_recurring_plan_redemption:
                recurring_redemptions += txn.total
                recurring_redemptions_count += 1
            else:
                retail += txn.total
                retail_count += 1

        sales_total = recurring_plan_sales + recurring_redemptions + retail
        sales_count = (
            recurring_plan_sales_count + recurring_redemptions_count + retail_count
        )

        sales = SalesResult(
            total=sales_total,
            count=sales_count,
            recurring_plan_sales=recurring_plan_sales,
            recurring_plan_sales_count=recurring_plan_sales_count,
            recurring_redemptions=recurring_redemptions,
            recurring_redemptions_count=recurring_redemptions_count,
            retail=retail,
            retail_count=retail_count,
        )

        # --- 3. Compute WashResult ---
        wash_count = len(wash_transactions)
        prepaid_wash_count = len(prepaid_transactions)

        washes = WashResult(
            total=wash_count + prepaid_wash_count,
            wash_count=wash_count,
            prepaid_wash_count=prepaid_wash_count,
        )

        # --- 4. Compute new_memberships ---
        activations = [c for c in status_changes if c.new_status == "Active"]
        new_memberships = len(activations)

        # --- 5. Compute ConversionResult ---
        retail_washes = wash_count
        total_opportunities = new_memberships + retail_washes
        rate = (
            new_memberships / total_opportunities
            if total_opportunities > 0
            else 0.0
        )

        conversion = ConversionResult(
            rate=rate,
            new_memberships=new_memberships,
            retail_washes=retail_washes,
            total_opportunities=total_opportunities,
        )

        # --- 6. Resolve period dates ---
        start_dt, end_dt = parse_date_range(start, end)
        period_start = start_dt.date().isoformat()
        period_end = end_dt.date().isoformat()

        # --- 7. Return unified report ---
        return StatsReport(
            sales=sales,
            washes=washes,
            new_memberships=new_memberships,
            conversion=conversion,
            period_start=period_start,
            period_end=period_end,
        )
