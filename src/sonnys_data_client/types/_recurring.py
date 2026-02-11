"""Recurring account response models."""

from pydantic import ConfigDict, Field

from sonnys_data_client.types._base import SonnysModel
from sonnys_data_client.types._washbooks import (
    WashbookCustomer,
    WashbookTag,
    WashbookVehicle,
)


class RecurringStatus(SonnysModel):
    """A status entry (status name + date) in a recurring account's history."""

    status: str
    date: str


class RecurringBilling(SonnysModel):
    """A billing entry in a recurring account's payment history.

    Contains charge amount, date, and last four digits of the credit card.
    """

    amount_charged: float
    date: str
    last_four_cc: str = Field(alias="lastFourCC")
    credit_card_expiration_date: str | None = None


class RecurringListItem(SonnysModel):
    """Summary recurring account returned by ``client.recurring.list()``.

    Contains ID, plan name, status, balance, and billing site.
    """

    id: str
    name: str | None = None
    balance: float | None = None
    sign_up_date: str
    cancel_date: str | None = None
    billing_site_id: int
    customer_id: str | None = None
    status: int
    status_name: str
    billing_site_code: str


class Recurring(SonnysModel):
    """Full recurring account detail returned by ``client.recurring.get(id)``.

    Includes customer, vehicles, tags, billing history, and status history.
    """

    id: str
    is_on_trial: bool
    trial_amount: float
    billing_site_code: str
    creation_site_code: str
    next_bill_date: str
    tags: list[WashbookTag]
    vehicles: list[WashbookVehicle]
    last_bill_date: str | None = None
    billing_amount: float | None = None
    is_suspended: bool
    suspended_until: str | None = None
    current_recurring_status_name: str
    plan_name: str
    customer: WashbookCustomer
    recurring_statuses: list[RecurringStatus]
    recurring_billings: list[RecurringBilling]
    additional_tag_price: float | None = None


class RecurringStatusChange(SonnysModel):
    """A status change event returned by ``client.recurring.list_status_changes()``.

    Records old/new status, date, employee, and site.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=None)

    washbook_account_id: str
    recurring_id: str
    old_status: str
    new_status: str
    status_date: str
    employee_name: str
    site_code: str


class RecurringModificationEntry(SonnysModel):
    """A single modification entry with name, date, and optional comment."""

    name: str
    date: str
    comment: str | None = None


class RecurringModification(Recurring):
    """A recurring account with its modification history.

    Extends :class:`Recurring` with a modifications list.
    Returned by ``client.recurring.list_modifications()``.
    """

    modifications: list[RecurringModificationEntry]
