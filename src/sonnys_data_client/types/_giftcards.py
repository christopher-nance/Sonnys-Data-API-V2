from sonnys_data_client.types._base import SonnysModel


class GiftcardListItem(SonnysModel):
    site_code: str
    complete_date: str | None = None
    number: str
    value: float
    amount_used: float
    giftcard_id: str
