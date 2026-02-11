"""Stats result models for business analytics."""

from sonnys_data_client.types._base import SonnysModel


class SalesResult(SonnysModel):
    """Revenue breakdown returned by ``client.stats.total_sales()``.

    Categorizes total revenue into three buckets based on transaction
    flags: recurring plan sales, recurring redemptions, and retail.
    Each bucket includes both a revenue total and a transaction count.
    """

    total: float
    count: int
    recurring_plan_sales: float
    recurring_plan_sales_count: int
    recurring_redemptions: float
    recurring_redemptions_count: int
    retail: float
    retail_count: int


class WashResult(SonnysModel):
    """Wash volume breakdown returned by ``client.stats.total_washes()``.

    Categorizes wash transactions into two types: retail washes
    (standard single-use transactions of type ``"wash"``) and prepaid
    washes (transactions of type ``"prepaid-wash"`` redeemed against
    pre-purchased wash books).  The ``total`` field is the sum of both.
    """

    total: int
    wash_count: int
    prepaid_wash_count: int


class ConversionResult(SonnysModel):
    """Membership conversion KPI returned by ``client.stats.conversion_rate()``.

    Measures how effectively a site converts retail wash customers into
    membership sign-ups.  The ``rate`` is computed as
    ``new_memberships / total_opportunities`` where total opportunities
    is the sum of new membership activations and retail wash transactions.

    A rate of ``0.15`` means 15 % of wash-or-membership interactions
    resulted in a new membership activation.  When there are zero
    opportunities the rate is ``0.0`` (division-by-zero safe).
    """

    rate: float
    new_memberships: int
    retail_washes: int
    total_opportunities: int


class StatsReport(SonnysModel):
    """Unified analytics report returned by ``client.stats.report()``.

    Bundles all KPIs into a single result object, computed from shared
    data fetches for efficiency.  Calling ``report()`` makes **4 API
    calls** instead of the **7** that would result from calling
    ``total_sales()``, ``total_washes()``, ``new_memberships_sold()``,
    and ``conversion_rate()`` individually.

    Attributes:
        sales: Revenue breakdown (recurring plan sales, recurring
            redemptions, and retail) as a :class:`SalesResult`.
        washes: Wash volume breakdown (retail washes and prepaid washes)
            as a :class:`WashResult`.
        new_memberships: Count of membership activations (transitions to
            ``"Active"`` status) during the report period.
        conversion: Membership conversion rate KPI as a
            :class:`ConversionResult`.
        period_start: ISO-8601 date string for the start of the report
            range (e.g. ``"2026-01-01"``).
        period_end: ISO-8601 date string for the end of the report
            range (e.g. ``"2026-01-31"``).
    """

    sales: SalesResult
    washes: WashResult
    new_memberships: int
    conversion: ConversionResult
    period_start: str
    period_end: str
