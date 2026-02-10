"""Sites resource."""

from __future__ import annotations

from sonnys_data_client._resources import ListableResource
from sonnys_data_client.types._sites import Site


class Sites(ListableResource):
    """Access the /site/list endpoint."""

    _path = "/site/list"
    _items_key = "sites"
    _model = Site
    _paginated = False
