"""Item response models."""

from sonnys_data_client.types._base import SonnysModel


class Item(SonnysModel):
    """A menu item (wash package, product, or service) returned by ``client.items.list()``.

    Includes SKU, pricing, and department info.
    """

    sku: str
    name: str
    department_name: str
    price_at_site: str
    cost_per_item: str | None = None
    is_prompt_for_price: bool
    site_location: str
