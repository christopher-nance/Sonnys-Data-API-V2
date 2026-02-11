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

    Categorizes wash transactions using v2 transaction flags:

    - **retail_wash_count**: Transactions where both
      ``is_recurring_plan_sale`` and ``is_recurring_plan_redemption``
      are ``False``.
    - **member_wash_count**: Transactions where
      ``is_recurring_plan_redemption`` is ``True`` (membership washes).
    - **eligible_wash_count**: Retail washes with ``total > 0``
      (excludes complimentary washes).  Used as the denominator in
      conversion rate calculations.

    The ``total`` field is the sum of retail and member wash counts.
    """

    total: int
    retail_wash_count: int
    member_wash_count: int
    eligible_wash_count: int
    free_wash_count: int


class ConversionResult(SonnysModel):
    """Membership conversion KPI returned by ``client.stats.conversion_rate()``.

    Measures how effectively a site converts eligible wash customers
    into membership sign-ups.  The ``rate`` is computed as
    ``new_memberships / eligible_washes``.

    A rate of ``0.15`` means 15 % of eligible washes resulted in a
    new membership sale.  When there are zero eligible washes the rate
    is ``0.0`` (division-by-zero safe).
    """

    rate: float
    new_memberships: int
    eligible_washes: int


class StatsReport(SonnysModel):
    """Unified analytics report returned by ``client.stats.report()``.

    Bundles all KPIs into a single result object, computed from a
    single v2 transaction fetch for efficiency.

    Attributes:
        sales: Revenue breakdown (recurring plan sales, recurring
            redemptions, and retail) as a :class:`SalesResult`.
        washes: Wash volume breakdown (retail, member, and eligible
            washes) as a :class:`WashResult`.
        new_memberships: Count of recurring plan sales during the
            report period.
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
