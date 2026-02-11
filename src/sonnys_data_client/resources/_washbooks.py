"""Washbooks resource."""

from __future__ import annotations

from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._washbooks import Washbook, WashbookListItem


class Washbooks(ListableResource, GettableResource):
    """Access the /washbook/account list and detail endpoints.

    Provides paginated washbook account search and individual account
    lookup with full detail.

    - ``list()`` returns :class:`~sonnys_data_client.types.WashbookListItem`
      summaries. Supports date and site filters.
    - ``get(id)`` returns a full :class:`~sonnys_data_client.types.Washbook`
      record with customer, vehicle, and tag details.
    """

    _path = "/washbook/account/list"
    _items_key = "accounts"
    _model = WashbookListItem
    _default_limit = 100
    _paginated = True

    _detail_path = "/washbook/account/{id}/detail"
    _detail_model = Washbook
