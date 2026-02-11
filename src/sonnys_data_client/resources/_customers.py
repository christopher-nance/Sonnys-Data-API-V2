"""Customers resource."""

from __future__ import annotations

from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._customers import Customer, CustomerListItem


class Customers(ListableResource, GettableResource):
    """Access the /customer list and detail endpoints.

    Provides paginated customer search and individual customer lookup.

    - ``list()`` returns :class:`~sonnys_data_client.types.CustomerListItem`
      summaries. Supports ``startDate``, ``endDate``, ``site``, and ``region``
      filters.
    - ``get(id)`` returns a full :class:`~sonnys_data_client.types.Customer`
      profile including address, contact info, and SMS preferences.
    """

    _path = "/customer"
    _items_key = "customers"
    _model = CustomerListItem
    _default_limit = 100
    _paginated = True

    _detail_path = "/customer/{id}"
    _detail_model = Customer
