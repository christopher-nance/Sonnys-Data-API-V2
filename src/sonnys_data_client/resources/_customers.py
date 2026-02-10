"""Customers resource."""

from __future__ import annotations

from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._customers import Customer, CustomerListItem


class Customers(ListableResource, GettableResource):
    """Access the /customer list and detail endpoints."""

    _path = "/customer"
    _items_key = "customers"
    _model = CustomerListItem
    _default_limit = 100
    _paginated = True

    _detail_path = "/customer/{id}"
    _detail_model = Customer
