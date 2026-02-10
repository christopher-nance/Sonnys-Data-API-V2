"""Giftcards resource."""

from __future__ import annotations

from sonnys_data_client._resources import ListableResource
from sonnys_data_client.types._giftcards import GiftcardListItem


class Giftcards(ListableResource):
    """Access the /giftcard-liablilty list endpoint."""

    _path = "/giftcard-liablilty"
    _items_key = "giftcards"
    _model = GiftcardListItem
    _default_limit = 100
    _paginated = True
