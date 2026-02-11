# Sonny's Data Client

A typed Python SDK for the Sonny's Carwash Controls Data API.

`sonnys-data-client` wraps the Sonny's Carwash Controls REST API with a
resource-based interface. Every response is returned as a validated Pydantic v2
model, list calls auto-paginate transparently, and a built-in rate limiter keeps
your application within the API's request window.

## Features

- **8 resource types** -- Customers, Employees, Giftcards, Items, Recurring Accounts, Sites, Transactions, and Washbooks
- **Auto-pagination** -- `.list()` calls transparently fetch all pages
- **Rate limiting** -- Built-in rate limiter with exponential-backoff retry
- **Pydantic v2 models** -- Fully typed responses with validation
- **Batch jobs** -- Long-running export operations with polling support

## Installation

```bash
pip install git+https://github.com/christopher-nance/Sonnys-Data-API-V2.git
```

## Quick Start

```python
from sonnys_data_client import SonnysClient

with SonnysClient(api_id="your-api-id", api_key="your-api-key") as client:
    transactions = client.transactions.list(
        startDate="2024-01-01", endDate="2024-01-31"
    )
    for txn in transactions:
        print(txn.transaction_id, txn.total)
```

## API Reference

- [Client](api/client.md) -- `SonnysClient` constructor and configuration
- [Resources](api/resources.md) -- Resource classes for each API endpoint
- [Models](api/models.md) -- Pydantic response models
- [Exceptions](api/exceptions.md) -- Error types and exception hierarchy
