from sonnys_data_client.types._base import SonnysModel


class ClockEntry(SonnysModel):
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
    first_name: str
    last_name: str
    employee_id: int


class Employee(SonnysModel):
    employee_id: int
    first_name: str
    last_name: str
    active: bool
    start_date: str
    start_date_change: str
    phone: str | None = None
    email: str | None = None
