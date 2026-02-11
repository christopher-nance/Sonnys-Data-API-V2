"""Giftcards resource."""

from __future__ import annotations

from sonnys_data_client._resources import ListableResource
from sonnys_data_client.types._giftcards import GiftcardListItem


class Giftcards(ListableResource):
    """Access the /giftcard-liablilty list endpoint.

    Provides paginated gift card liability listing. List-only resource
    with no detail endpoint.

    - ``list()`` returns :class:`~sonnys_data_client.types.GiftcardListItem`
      records with balance and usage info.

    Note:
        The API path contains a typo (``giftcard-liablilty``) which is
        intentional to match the actual Sonny's API endpoint.
    """

    _path = "/giftcard-liablilty"
    _items_key = "giftcards"
    _model = GiftcardListItem
    _default_limit = 100
    _paginated = True
