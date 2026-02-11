"""Sites resource."""

from __future__ import annotations

from sonnys_data_client._resources import ListableResource
from sonnys_data_client.types._sites import Site


class Sites(ListableResource):
    """Access the /site/list endpoint.

    Provides a complete site listing. Non-paginated resource that returns
    all sites in a single call. No detail endpoint.

    - ``list()`` returns :class:`~sonnys_data_client.types.Site` records
      with site ID, code, name, and timezone.
    """

    _path = "/site/list"
    _items_key = "sites"
    _model = Site
    _paginated = False
