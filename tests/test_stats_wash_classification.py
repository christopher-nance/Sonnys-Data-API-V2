"""Tests for wash classification in StatsResource.total_washes / report.

These exercise the regression where transactions that are neither
``type=wash`` nor ``type=recurring`` (e.g. prepaid gift card sales,
prepaid membership sales) were being counted as retail washes by an
``unknown non-negative type`` fallback. Verified against the BackOffice
"Sales Overview V2 Report" for FRVW on 2026-05-06: BackOffice reported
15 Total Cars / 2 Net Cars; the API client reported 21 / 7 because the
fallback swept in 6 prepaid sales.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from sonnys_data_client._client import SonnysClient
from sonnys_data_client.resources._stats import StatsResource
from sonnys_data_client.types._transactions import (
    TransactionListItem,
    TransactionV2ListItem,
)


def _make_stats() -> StatsResource:
    client = SonnysClient("id", "key")
    client._rate_limiter.acquire = MagicMock(return_value=0.0)
    stats = StatsResource(client)
    # Bypass site-timezone lookup; tests stub _resolve_dates directly.
    stats._resolve_dates = MagicMock(return_value={"startDate": 0, "endDate": 1})
    return stats


def _v1_wash(trans_id: str, total: float) -> TransactionListItem:
    return TransactionListItem(
        trans_number=int(trans_id.split(":")[0]),
        trans_id=trans_id,
        total=total,
        date="2026-05-06",
    )


def _v2(
    trans_id: str,
    total: float,
    *,
    plan_sale: bool = False,
    redemption: bool = False,
) -> TransactionV2ListItem:
    return TransactionV2ListItem(
        trans_number=int(trans_id.split(":")[0]),
        trans_id=trans_id,
        total=total,
        date="2026-05-06",
        customer_id=None,
        is_recurring_plan_sale=plan_sale,
        is_recurring_plan_redemption=redemption,
        transaction_status="Completed",
    )


class TestTotalWashesPrepaidExclusion:
    """Prepaid sales (no wash, no recurring, no plan-sale flag) must not be washes."""

    def test_prepaid_sale_is_not_counted_as_retail_wash(self) -> None:
        stats = _make_stats()

        # 1 retail wash, 1 plan-sale wash, 1 redemption, 1 recharge,
        # 2 prepaid sales (no flags, not in wash_ids, not in recurring_ids)
        wash_v1 = [_v1_wash("100:1", 13.0), _v1_wash("200:1", 10.0)]
        recurring_v1 = [_v1_wash("300:1", 55.0)]  # recharge (not a wash)
        v2 = [
            _v2("100:1", 13.0),                           # retail wash
            _v2("200:1", 10.0, plan_sale=True),           # plan-sale wash
            _v2("400:1", 13.0, redemption=True),          # member redemption
            _v2("300:1", 55.0),                           # recharge (in recurring_ids)
            _v2("500:1", 50.0),                           # prepaid sale (gift card)
            _v2("600:1", 25.0),                           # prepaid sale (gift card)
        ]

        def _fake_by_type(start, end, item_type):
            return wash_v1 if item_type == "wash" else recurring_v1

        stats._fetch_transactions_by_type = MagicMock(side_effect=_fake_by_type)
        stats._fetch_transactions_v2 = MagicMock(return_value=v2)

        result = stats.total_washes("2026-05-06", "2026-05-06")

        assert result.total == 3, (
            f"Expected 3 cars (1 retail + 1 plan-sale + 1 redemption); "
            f"got {result.total}. Prepaid sales must not count as washes."
        )
        assert result.retail_wash_count == 1
        assert result.member_wash_count == 1


class TestReportPrepaidExclusion:
    """The mirror branch in report() must also exclude prepaid sales."""

    def test_prepaid_sale_is_not_counted_in_report_washes(self) -> None:
        stats = _make_stats()

        wash_v1 = [_v1_wash("100:1", 13.0), _v1_wash("200:1", 10.0)]
        recurring_v1 = [_v1_wash("300:1", 55.0)]
        v2 = [
            _v2("100:1", 13.0),
            _v2("200:1", 10.0, plan_sale=True),
            _v2("400:1", 13.0, redemption=True),
            _v2("300:1", 55.0),
            _v2("500:1", 50.0),
            _v2("600:1", 25.0),
        ]

        def _fake_by_type(start, end, item_type):
            return wash_v1 if item_type == "wash" else recurring_v1

        stats._fetch_transactions_by_type = MagicMock(side_effect=_fake_by_type)
        stats._fetch_transactions_v2 = MagicMock(return_value=v2)
        stats._genuine_plan_sale_ids = MagicMock(return_value={"200:1"})
        stats._fetch_all_clock_entries = MagicMock(return_value=[])

        rpt = stats.report("2026-05-06", "2026-05-06")

        assert rpt.washes.total == 3, (
            f"Expected 3 cars in report; got {rpt.washes.total}. "
            f"Prepaid sales must not count as washes."
        )
        assert rpt.washes.retail_wash_count == 1
        assert rpt.washes.member_wash_count == 1
