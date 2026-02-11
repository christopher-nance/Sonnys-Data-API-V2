"""Giftcard response models."""

from sonnys_data_client.types._base import SonnysModel


class GiftcardListItem(SonnysModel):
    """A giftcard liability record returned by ``client.giftcards.list()``.

    Contains card number, value, amount used, and site code.
    """

    site_code: str
    complete_date: str | None = None
    number: str
    value: float
    amount_used: float
    giftcard_id: str
