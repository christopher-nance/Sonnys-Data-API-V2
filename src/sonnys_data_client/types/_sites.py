from pydantic import Field

from sonnys_data_client.types._base import SonnysModel


class Site(SonnysModel):
    site_id: int = Field(alias="siteID")
    code: str | None = None
    name: str
    timezone: str | None = None
