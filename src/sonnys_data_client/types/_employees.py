"""Employee response models."""

from sonnys_data_client.types._base import SonnysModel


class ClockEntry(SonnysModel):
    """A single clock-in/clock-out record for an employee.

    Returned by ``client.employees.get_clock_entries()``.
    """

    clock_in: str | None = None
    clock_out: str | None = None
    regular_rate: float
    regular_hours: float
    overtime_eligible: bool
    overtime_rate: float
    overtime_hours: float
    was_modified: bool
    modification_timestamp: str | None = None
    was_created_in_back_office: bool
    site_code: str


class EmployeeListItem(SonnysModel):
    """Summary employee record returned by ``client.employees.list()``.

    Contains name and employee ID.
    """

    first_name: str
    last_name: str
    employee_id: int


class Employee(SonnysModel):
    """Full employee profile returned by ``client.employees.get(id)``.

    Includes contact info, active status, and start date.
    """

    employee_id: int
    first_name: str
    last_name: str
    active: bool
    start_date: str
    start_date_change: str | None = None
    phone: str | None = None
    email: str | None = None
