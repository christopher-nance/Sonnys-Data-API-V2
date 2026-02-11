# Employees

The **Employees** resource provides access to employee records and their clock
entry history. Beyond the standard `list()` and `get()` methods, this resource
includes a dedicated `get_clock_entries()` method for retrieving time-tracking
data with date range filtering.

## Methods

### `list(**params) -> list[EmployeeListItem]`

Fetch all employees. Returns a list of `EmployeeListItem` objects with summary
fields. The client automatically paginates through all pages of results.

```python
employees = client.employees.list()
```

### `get(employee_id) -> Employee`

Fetch full details for a single employee by their ID. Returns an `Employee`
object with all fields including active status, start date, phone, and email.

```python
employee = client.employees.get("42")
```

### `get_clock_entries(employee_id, *, start_date=None, end_date=None) -> list[ClockEntry]`

Fetch clock entries for a specific employee. Returns a flat list of `ClockEntry`
objects. Optionally filter by date range using `start_date` and `end_date`.

```python
entries = client.employees.get_clock_entries(
    "42",
    start_date="2025-01-01",
    end_date="2025-01-31",
)
```

!!! note "Keyword-only arguments"
    `start_date` and `end_date` are keyword-only arguments. They must be passed
    by name, not by position. These are passed to the API as `startDate` and
    `endDate` query parameters.

## Examples

### List all employees

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    employees = client.employees.list()

    for emp in employees:
        print(f"{emp.first_name} {emp.last_name} (ID: {emp.employee_id})")
```

### Get employee detail

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    emp = client.employees.get("42")

    print(f"Name:       {emp.first_name} {emp.last_name}")
    print(f"Active:     {emp.active}")
    print(f"Start Date: {emp.start_date}")
    print(f"Phone:      {emp.phone}")
    print(f"Email:      {emp.email}")
```

### Fetch clock entries for a date range

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    entries = client.employees.get_clock_entries(
        "42",
        start_date="2025-06-01",
        end_date="2025-06-14",
    )

    print(f"Found {len(entries)} clock entries\n")

    for entry in entries:
        print(f"Site:     {entry.site_code}")
        print(f"Clock In: {entry.clock_in}")
        print(f"Clock Out:{entry.clock_out}")
        print(f"Regular:  {entry.regular_hours}h @ ${entry.regular_rate}/h")
        print(f"Overtime: {entry.overtime_hours}h @ ${entry.overtime_rate}/h")
        print(f"Modified: {entry.was_modified}")
        print()
```

### Summarize hours for all employees

```python
with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    employees = client.employees.list()

    for emp in employees:
        entries = client.employees.get_clock_entries(
            str(emp.employee_id),
            start_date="2025-06-01",
            end_date="2025-06-14",
        )

        total_regular = sum(e.regular_hours for e in entries)
        total_overtime = sum(e.overtime_hours for e in entries)

        print(
            f"{emp.first_name} {emp.last_name}: "
            f"{total_regular:.1f}h regular, {total_overtime:.1f}h overtime"
        )
```

## Models

### `EmployeeListItem`

Returned by `list()`. Contains summary fields for each employee.

| Field         | Type  | Description                |
|---------------|-------|----------------------------|
| `first_name`  | `str` | Employee first name        |
| `last_name`   | `str` | Employee last name         |
| `employee_id` | `int` | Unique employee identifier |

### `Employee`

Returned by `get()`. Contains full employee details.

| Field               | Type           | Description                     |
|---------------------|----------------|---------------------------------|
| `employee_id`       | `int`          | Unique employee identifier      |
| `first_name`        | `str`          | Employee first name             |
| `last_name`         | `str`          | Employee last name              |
| `active`            | `bool`         | Whether the employee is active  |
| `start_date`        | `str`          | Employment start date           |
| `start_date_change` | `str \| None`  | Date the start date was changed |
| `phone`             | `str \| None`  | Phone number                    |
| `email`             | `str \| None`  | Email address                   |

### `ClockEntry`

Returned by `get_clock_entries()`. Represents a single clock-in/clock-out record.

| Field                       | Type           | Description                            |
|-----------------------------|----------------|----------------------------------------|
| `clock_in`                  | `str \| None`  | Clock-in timestamp                     |
| `clock_out`                 | `str \| None`  | Clock-out timestamp                    |
| `regular_rate`              | `float`        | Hourly pay rate for regular hours      |
| `regular_hours`             | `float`        | Number of regular hours worked         |
| `overtime_eligible`         | `bool`         | Whether the employee is OT-eligible    |
| `overtime_rate`             | `float`        | Hourly pay rate for overtime hours     |
| `overtime_hours`            | `float`        | Number of overtime hours worked        |
| `was_modified`              | `bool`         | Whether the entry was manually edited  |
| `modification_timestamp`    | `str \| None`  | When the entry was modified            |
| `was_created_in_back_office`| `bool`         | Whether the entry was created in back office |
| `site_code`                 | `str`          | Site code where the shift occurred     |

!!! info "Flattened response"
    The Sonny's API returns clock entries in a nested `weeks[].clockEntries[]`
    structure. The `get_clock_entries()` method automatically flattens this into
    a single list of `ClockEntry` objects for easier iteration.

!!! note "Auto-pagination"
    The `list()` method automatically fetches all pages of results. You do not
    need to handle pagination manually -- the client will continue requesting
    pages until all records have been retrieved.

!!! tip "Full model reference"
    For the complete field definitions and type annotations, see the
    [Models](../api/models.md) page in the API Reference.
