"""Employees resource."""

from __future__ import annotations

from sonnys_data_client._resources import GettableResource, ListableResource
from sonnys_data_client.types._employees import ClockEntry, Employee, EmployeeListItem


class Employees(ListableResource, GettableResource):
    """Access the /employee list and detail endpoints.

    Provides paginated employee search, individual employee lookup, and
    time-tracking data.

    - ``list()`` returns :class:`~sonnys_data_client.types.EmployeeListItem`
      summaries. Supports ``startDate`` and ``endDate`` filters.
    - ``get(id)`` returns a full :class:`~sonnys_data_client.types.Employee`
      record with contact info and employment dates.
    - ``get_clock_entries(id)`` fetches
      :class:`~sonnys_data_client.types.ClockEntry` time-tracking records
      for a specific employee.
    """

    _path = "/employee"
    _items_key = "employees"
    _model = EmployeeListItem
    _default_limit = 100
    _paginated = True

    _detail_path = "/employee/{id}"
    _detail_model = Employee

    def get_clock_entries(
        self,
        employee_id: int | str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[ClockEntry]:
        """Fetch clock entries for an employee.

        The API returns a nested ``data.weeks[]`` structure where each week
        contains a ``clockEntries[]`` array.  This method flattens them into
        a single list.

        Args:
            employee_id: The employee identifier.
            start_date: Optional start date filter (passed as ``startDate``).
            end_date: Optional end date filter (passed as ``endDate``).

        Returns:
            A flat list of validated :class:`ClockEntry` instances.
        """
        params: dict[str, str] = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        response = self._client._request(
            "GET",
            f"/employee/{employee_id}/clock-entries",
            params=params,
        )
        data = response.json()["data"]

        entries: list[ClockEntry] = []
        for week in data["weeks"]:
            for entry in week["clockEntries"]:
                entries.append(ClockEntry.model_validate(entry))
        return entries
