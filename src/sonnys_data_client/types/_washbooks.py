from sonnys_data_client.types._base import SonnysModel


class WashbookTag(SonnysModel):
    id: str
    number: str
    enabled: bool


class WashbookVehicle(SonnysModel):
    id: str
    plate: str | None = None


class WashbookCustomer(SonnysModel):
    id: str | None = None
    number: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class WashbookRecurringInfo(SonnysModel):
    current_billable_amount: float
    next_bill_date: str | None = None
    last_bill_date: str | None = None
    is_on_trial: bool
    remaining_trial_periods: int


class WashbookListItem(SonnysModel):
    id: str
    name: str | None = None
    balance: str
    sign_up_date: str
    cancel_date: str | None = None
    billing_site_id: int
    customer_id: str | None = None
    status: str


class Washbook(SonnysModel):
    id: str
    name: str
    balance: str | None = None
    customer: WashbookCustomer
    status: str
    recurring_info: WashbookRecurringInfo
    tags: list[WashbookTag]
    vehicles: list[WashbookVehicle]
