"""Core client for the Sonny's Carwash Controls Data API."""

from __future__ import annotations

import requests


class SonnysClient:
    """Client for the Sonny's Carwash Controls Data API.

    Manages authentication and HTTP session lifecycle. Use as a context
    manager or call :meth:`close` explicitly when done.

    Args:
        api_id: Sonny's API ID credential.
        api_key: Sonny's API key credential.
        site_code: Optional site code to scope requests to a specific site.
    """

    BASE_URL = "https://trigonapi.sonnyscontrols.com/v1"

    def __init__(
        self,
        api_id: str,
        api_key: str,
        site_code: str | None = None,
    ) -> None:
        self.api_id = api_id
        self.api_key = api_key
        self.site_code = site_code

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-Sonnys-API-ID": api_id,
                "X-Sonnys-API-Key": api_key,
            }
        )
        if site_code is not None:
            self._session.headers["X-Sonnys-Site-Code"] = site_code

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> SonnysClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"SonnysClient(base_url='{self.BASE_URL}')"
