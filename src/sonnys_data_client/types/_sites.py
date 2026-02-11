"""Site response models."""

from pydantic import Field

from sonnys_data_client.types._base import SonnysModel


class Site(SonnysModel):
    """A car wash site/location returned by ``client.sites.list()``.

    Contains the site code, name, and timezone.
    """

    site_id: int = Field(alias="siteID")
    code: str | None = None
    name: str
    timezone: str | None = None
