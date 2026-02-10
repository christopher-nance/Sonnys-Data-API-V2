"""Sonny's Carwash Controls Data API client."""

from sonnys_data_client._client import SonnysClient
from sonnys_data_client._version import __version__
from sonnys_data_client.resources import Customers, Items

from sonnys_data_client._exceptions import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
    SonnysError,
    ValidationError,
)

__all__ = [
    "SonnysClient",
    "__version__",
    "Customers",
    "Items",
    "APIConnectionError",
    "APIError",
    "APIStatusError",
    "APITimeoutError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "SonnysError",
    "ValidationError",
]
