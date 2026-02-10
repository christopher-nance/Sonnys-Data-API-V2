"""Items resource."""

from __future__ import annotations

from sonnys_data_client._resources import ListableResource
from sonnys_data_client.types._items import Item


class Items(ListableResource):
    """Access the /item list endpoint."""

    _path = "/item"
    _items_key = "items"
    _model = Item
    _default_limit = 100
    _paginated = True
