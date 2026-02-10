# Exceptions

All exceptions raised by the SDK inherit from `SonnysError`. The hierarchy is:

```
SonnysError
  APIError
    APIConnectionError
      APITimeoutError
    APIStatusError
      AuthError
      RateLimitError
      ValidationError
      NotFoundError
      ServerError
```

Catch `SonnysError` to handle any SDK error, or catch specific subclasses for
fine-grained control:

```python
from sonnys_data_client import SonnysClient, AuthError, RateLimitError, SonnysError

try:
    client.customers.list()
except AuthError:
    print("Invalid credentials")
except RateLimitError:
    print("Too many requests")
except SonnysError:
    print("Something else went wrong")
```

---

::: sonnys_data_client.SonnysError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.APIError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.APIConnectionError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.APITimeoutError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.APIStatusError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.AuthError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.RateLimitError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.ValidationError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.NotFoundError
    options:
      show_source: false
      heading_level: 2

::: sonnys_data_client.ServerError
    options:
      show_source: false
      heading_level: 2
