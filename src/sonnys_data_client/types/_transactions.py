"""Transaction response models."""

from pydantic import Field

from sonnys_data_client.types._base import SonnysModel


class TransactionTender(SonnysModel):
    """A payment tender (cash, credit, etc.) within a transaction detail.

    Contains tender type, amount, change, and optional credit card info.
    """

    tender: str
    tender_sub_type: str | None = None
    amount: float
    change: float
    total: float
    reference_number: str | None = None
    credit_card_last_four: str | None = None
    credit_card_expiration_date: str | None = None


class TransactionItem(SonnysModel):
    """A line item within a transaction detail.

    Contains the item name, SKU, department, quantity, and price breakdown
    (gross, net, discount, tax).
    """

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
    """A discount applied within a transaction detail.

    Records the discount name, code, amount, and which item it was applied to.
    """

    discount_name: str
    discount_sku: str | None = None
    applied_to_item_name: str
    discount_amount: float
    discount_code: str


class TransactionListItem(SonnysModel):
    """Summary transaction record returned by ``client.transactions.list()`` and ``client.transactions.list_by_type()``.

    Contains transaction number, ID, total, and date.
    """

    trans_number: int
    trans_id: str
    total: float
    date: str


class TransactionV2ListItem(TransactionListItem):
    """Enriched transaction summary returned by ``client.transactions.list_v2()``.

    Extends :class:`TransactionListItem` with customer ID, recurring plan flags,
    and transaction status.
    """

    customer_id: str | None = None
    is_recurring_plan_sale: bool
    is_recurring_plan_redemption: bool
    transaction_status: str


class Transaction(SonnysModel):
    """Full transaction detail returned by ``client.transactions.get(id)``.

    Includes line items, tenders, discounts, customer/employee info, and
    prepaid/recurring flags.
    """

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
    """Transaction record returned by ``client.transactions.load_job()``.

    Extends :class:`Transaction` with additional fields from the batch job
    endpoint.
    """

    customer_id: str | None = None
    is_recurring_plan_sale: bool | None = None
    is_recurring_plan_redemption: bool | None = None
    transaction_status: str | None = None
