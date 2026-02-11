"""Customer response models."""

from sonnys_data_client.types._base import SonnysModel


class Address(SonnysModel):
    """Mailing address for a customer."""

    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None


class CustomerListItem(SonnysModel):
    """Summary customer record returned by ``client.customers.list()``.

    Contains identifiers, name, phone, and active status.
    """

    customer_id: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    customer_number: str | None = None
    is_active: bool
    created_date: str
    modified_date: str | None = None


class Customer(SonnysModel):
    """Full customer profile returned by ``client.customers.get(id)``.

    Includes address, contact details, loyalty info, and SMS opt-in status.
    """

    id: str
    number: str
    first_name: str
    last_name: str
    company_name: str | None = None
    loyalty_number: str | None = None
    address: Address
    phone: str
    email: str | None = None
    birth_date: str | None = None
    is_active: bool
    allow_sms: bool
    recurring_sms_signup_date: str | None = None
    loyalty_sms_signup_date: str | None = None
    modify_date: str
