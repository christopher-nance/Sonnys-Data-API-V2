"""Washbook response models."""

from sonnys_data_client.types._base import SonnysModel


class WashbookTag(SonnysModel):
    """An RFID tag or barcode associated with a washbook account."""

    id: str
    number: str
    enabled: bool


class WashbookVehicle(SonnysModel):
    """A vehicle linked to a washbook account."""

    id: str
    plate: str | None = None


class WashbookCustomer(SonnysModel):
    """Customer info embedded in a washbook or recurring account detail."""

    id: str | None = None
    number: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class WashbookRecurringInfo(SonnysModel):
    """Recurring billing details embedded in a washbook detail.

    Includes billing amount, next/last bill dates, and trial status.
    """

    current_billable_amount: float
    next_bill_date: str | None = None
    last_bill_date: str | None = None
    is_on_trial: bool
    remaining_trial_periods: int


class WashbookListItem(SonnysModel):
    """Summary washbook record returned by ``client.washbooks.list()``.

    Contains ID, balance, status, and sign-up date.
    """

    id: str
    name: str | None = None
    balance: str
    sign_up_date: str
    cancel_date: str | None = None
    billing_site_id: int
    customer_id: str | None = None
    status: str


class Washbook(SonnysModel):
    """Full washbook detail returned by ``client.washbooks.get(id)``.

    Includes customer, vehicles, tags, and recurring billing info.
    """

    id: str
    name: str
    balance: str | None = None
    customer: WashbookCustomer
    status: str
    recurring_info: WashbookRecurringInfo
    tags: list[WashbookTag]
    vehicles: list[WashbookVehicle]
