from pydantic import Field

from sonnys_data_client.types._base import SonnysModel


class TransactionTender(SonnysModel):
    tender: str
    tender_sub_type: str | None = None
    amount: float
    change: float
    total: float
    reference_number: str | None = None
    credit_card_last_four: str | None = None
    credit_card_expiration_date: str | None = None


class TransactionItem(SonnysModel):
    name: str
    sku: str | None = None
    department: str
    quantity: int
    gross: float
    net: float
    discount: float
    tax: float
    additional_fee: float
    is_voided: bool


class TransactionDiscount(SonnysModel):
    discount_name: str
    discount_sku: str | None = None
    applied_to_item_name: str
    discount_amount: float
    discount_code: str


class TransactionListItem(SonnysModel):
    trans_number: int
    trans_id: str
    total: float
    date: str


class TransactionV2ListItem(TransactionListItem):
    customer_id: str | None = None
    is_recurring_plan_sale: bool
    is_recurring_plan_redemption: bool
    transaction_status: str


class Transaction(SonnysModel):
    id: str
    number: int
    type: str
    complete_date: str
    location_code: str
    sales_device_name: str
    total: float
    tenders: list[TransactionTender]
    items: list[TransactionItem]
    customer_name: str | None = None
    customer_id: str | None = None
    vehicle_license_plate: str | None = None
    employee_cashier: str | None = None
    employee_greeter: str | None = None
    discounts: list[TransactionDiscount] = Field(alias="discount")
    is_recurring_payment: bool
    is_recurring_redemption: bool
    is_recurring_sale: bool
    is_prepaid_redemption: bool
    is_prepaid_sale: bool


class TransactionJobItem(Transaction):
    customer_id: str | None = None
    is_recurring_plan_sale: bool | None = None
    is_recurring_plan_redemption: bool | None = None
    transaction_status: str | None = None
