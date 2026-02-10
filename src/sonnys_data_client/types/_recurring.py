from pydantic import ConfigDict, Field

from sonnys_data_client.types._base import SonnysModel
from sonnys_data_client.types._washbooks import (
    WashbookCustomer,
    WashbookTag,
    WashbookVehicle,
)


class RecurringStatus(SonnysModel):
    status: str
    date: str


class RecurringBilling(SonnysModel):
    amount_charged: float
    date: str
    last_four_cc: str = Field(alias="lastFourCC")
    credit_card_expiration_date: str | None = None


class RecurringListItem(SonnysModel):
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
    model_config = ConfigDict(populate_by_name=True, alias_generator=None)

    washbook_account_id: str
    recurring_id: str
    old_status: str
    new_status: str
    status_date: str
    employee_name: str
    site_code: str


class RecurringModificationEntry(SonnysModel):
    modification_type: str
    modification_date: str
    modification_comment: str | None = None


class RecurringModification(Recurring):
    modifications: list[RecurringModificationEntry]
