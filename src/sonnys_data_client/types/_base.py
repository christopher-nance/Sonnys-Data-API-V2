"""Base model for all Sonny's Data Client response types."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class SonnysModel(BaseModel):
    """Base Pydantic model for all API response types.

    Configures camelCase alias generation so API responses (camelCase)
    map to Pythonic snake_case attributes.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )
