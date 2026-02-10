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
    discount: float
    discount_code: str
