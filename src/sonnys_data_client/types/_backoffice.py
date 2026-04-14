"""BackOffice scraper response models.

These models are populated by parsing the HTML of the Sonny's BackOffice
``/report/employee-timesheets`` page rather than a JSON API response.
Field naming is deliberately snake_case and ``populate_by_name=True``
on :class:`SonnysModel` lets construction by keyword work.
"""

from sonnys_data_client.types._base import SonnysModel


class TimesheetShift(SonnysModel):
    """A single punch-in/punch-out shift for one employee.

    One BackOffice detail row = one shift. Employees can have multiple
    shifts per day, potentially at different sites.

    When an employee is still clocked in at the moment the report was
    rendered (i.e. the shift is in progress), ``date_out`` and
    ``time_out`` are ``None``. Use :attr:`is_open` to test for this
    cleanly. BackOffice still reports ``regular_hours``, ``regular_wages``,
    and ``total_wages`` for open shifts based on elapsed time up to the
    moment the page was rendered.
    """

    date_in: str
    time_in: str
    date_out: str | None = None
    time_out: str | None = None
    timezone: str
    site_code: str
    regular_rate: float
    regular_hours: float
    regular_wages: float
    overtime_rate: float | None = None
    overtime_hours: float | None = None
    overtime_wages: float | None = None
    total_wages: float
    was_modified: bool = False
    was_created_in_back_office: bool = False
    comment: str | None = None

    @property
    def is_open(self) -> bool:
        """``True`` when the shift has no clock-out yet (employee is
        still on the clock at the moment the report was rendered)."""
        return self.date_out is None


class EmployeeTimesheet(SonnysModel):
    """All shifts for one employee in the reporting period, plus their
    per-employee rollup totals from the "Total for <name>:" row.
    """

    employee_name: str
    employee_number: int
    adp_id: str | None = None
    shifts: list[TimesheetShift]
    total_regular_hours: float
    total_regular_wages: float
    total_overtime_hours: float | None = None
    total_overtime_wages: float | None = None
    total_wages: float


class BackOfficeTimeclockResult(SonnysModel):
    """Complete employee-timesheets / timeclock report for a date range.

    Returned by :meth:`BackOfficeResource.timeclock`. Contains per-shift
    detail nested under per-employee rollups, plus grand totals parsed
    from the final "Timesheet Total:" footer row.
    """

    period_start: str
    period_end: str
    employees: list[EmployeeTimesheet]
    total_regular_hours: float
    total_regular_wages: float
    total_overtime_hours: float
    total_overtime_wages: float
    total_wages: float
