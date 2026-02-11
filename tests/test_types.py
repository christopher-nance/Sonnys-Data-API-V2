"""Validation tests for all Pydantic v2 response models."""

import sonnys_data_client.types as types


class TestSonnysModelBase:
    """Tests for the SonnysModel base class behavior."""

    def test_alias_generator_produces_camel_case(self):
        """SonnysModel subclasses should serialize field names as camelCase."""
        item = types.Item(
            sku="W001",
            name="Basic Wash",
            department_name="Washes",
            price_at_site="9.99",
            is_prompt_for_price=False,
            site_location="MAIN",
        )
        dumped = item.model_dump(by_alias=True)
        assert "departmentName" in dumped
        assert "priceAtSite" in dumped
        assert "isPromptForPrice" in dumped
        assert "siteLocation" in dumped

    def test_populate_by_name_allows_snake_case_input(self):
        """Models should accept both snake_case and camelCase field names."""
        item_snake = types.Item(
            sku="W001",
            name="Basic Wash",
            department_name="Washes",
            price_at_site="9.99",
            is_prompt_for_price=False,
            site_location="MAIN",
        )
        item_camel = types.Item(
            **{
                "sku": "W001",
                "name": "Basic Wash",
                "departmentName": "Washes",
                "priceAtSite": "9.99",
                "isPromptForPrice": False,
                "siteLocation": "MAIN",
            }
        )
        assert item_snake.department_name == item_camel.department_name

    def test_sonnys_model_in_all(self):
        """SonnysModel itself should be exported."""
        assert "SonnysModel" in types.__all__


class TestTransactionModels:
    """Tests for Transaction-related models."""

    def test_transaction_v2_list_item_from_camel_case(self):
        """TransactionV2ListItem should parse camelCase API response data."""
        data = {
            "transNumber": 100,
            "transId": "1:2",
            "total": 10.0,
            "date": "2020-01-01",
            "customerId": None,
            "isRecurringPlanSale": False,
            "isRecurringPlanRedemption": False,
            "transactionStatus": "Completed",
        }
        obj = types.TransactionV2ListItem(**data)
        assert obj.trans_number == 100
        assert obj.trans_id == "1:2"
        assert obj.total == 10.0
        assert obj.customer_id is None
        assert obj.is_recurring_plan_sale is False
        assert obj.transaction_status == "Completed"

    def test_transaction_with_nested_tenders_and_items(self):
        """Transaction should parse nested tenders and items arrays."""
        data = {
            "id": "abc-123",
            "number": 42,
            "type": "Sale",
            "completeDate": "2024-06-15T10:30:00",
            "locationCode": "MAIN",
            "salesDeviceName": "POS-1",
            "total": 25.99,
            "tenders": [
                {
                    "tender": "Credit",
                    "tenderSubType": "Visa",
                    "amount": 25.99,
                    "change": 0.0,
                    "total": 25.99,
                    "referenceNumber": "REF001",
                    "creditCardLastFour": "4242",
                    "creditCardExpirationDate": "12/26",
                }
            ],
            "items": [
                {
                    "name": "Premium Wash",
                    "sku": "PW01",
                    "department": "Washes",
                    "quantity": 1,
                    "gross": 25.99,
                    "net": 23.99,
                    "discount": 2.0,
                    "tax": 1.92,
                    "additionalFee": 0.0,
                    "isVoided": False,
                }
            ],
            "discounts": [],
            "isRecurringPayment": False,
            "isRecurringRedemption": False,
            "isRecurringSale": False,
            "isPrepaidRedemption": False,
            "isPrepaidSale": False,
        }
        txn = types.Transaction(**data)
        assert txn.id == "abc-123"
        assert len(txn.tenders) == 1
        assert txn.tenders[0].credit_card_last_four == "4242"
        assert len(txn.items) == 1
        assert txn.items[0].name == "Premium Wash"
        assert txn.items[0].is_voided is False

    def test_transaction_list_item(self):
        """TransactionListItem should parse basic list data."""
        data = {
            "transNumber": 55,
            "transId": "5:10",
            "total": 15.0,
            "date": "2024-01-15",
        }
        obj = types.TransactionListItem(**data)
        assert obj.trans_number == 55
        assert obj.trans_id == "5:10"

    def test_transaction_discount(self):
        """TransactionDiscount should parse correctly."""
        data = {
            "discountName": "Senior Discount",
            "appliedToItemName": "Basic Wash",
            "discountAmount": 2.50,
            "discountCode": "SENIOR10",
        }
        obj = types.TransactionDiscount(**data)
        assert obj.discount_name == "Senior Discount"
        assert obj.discount_sku is None


class TestCustomerModels:
    """Tests for Customer-related models."""

    def test_customer_list_item_from_camel_case(self):
        """CustomerListItem should parse camelCase data."""
        data = {
            "customerId": "cust-001",
            "firstName": "Jane",
            "lastName": "Doe",
            "phoneNumber": "555-1234",
            "isActive": True,
            "createdDate": "2023-01-01",
            "modifiedDate": "2024-06-01",
        }
        obj = types.CustomerListItem(**data)
        assert obj.first_name == "Jane"
        assert obj.customer_id == "cust-001"
        assert obj.is_active is True

    def test_customer_with_nested_address(self):
        """Customer should parse with nested Address object."""
        data = {
            "id": "cust-002",
            "number": "C100",
            "firstName": "John",
            "lastName": "Smith",
            "companyName": "Acme Corp",
            "loyaltyNumber": "L999",
            "address": {
                "address1": "123 Main St",
                "city": "Springfield",
                "state": "MO",
                "postalCode": "65801",
            },
            "phone": "555-9999",
            "email": "john@acme.com",
            "isActive": True,
            "allowSms": False,
            "modifyDate": "2024-03-15",
        }
        cust = types.Customer(**data)
        assert cust.first_name == "John"
        assert cust.address.city == "Springfield"
        assert cust.address.postal_code == "65801"
        assert cust.email == "john@acme.com"


class TestAccountModels:
    """Tests for Washbook and Recurring models."""

    def test_washbook_with_nested_objects(self):
        """Washbook should parse nested customer, tags, vehicles, recurringInfo."""
        data = {
            "id": "wb-001",
            "name": "Monthly Plan",
            "balance": "50.00",
            "customer": {
                "id": "cust-100",
                "number": "C100",
                "firstName": "Alice",
                "lastName": "Jones",
            },
            "status": "Active",
            "recurringInfo": {
                "currentBillableAmount": 29.99,
                "nextBillDate": "2024-07-01",
                "lastBillDate": "2024-06-01",
                "isOnTrial": False,
                "remainingTrialPeriods": 0,
            },
            "tags": [{"id": "tag-1", "number": "T001", "enabled": True}],
            "vehicles": [{"id": "veh-1", "plate": "ABC123"}],
        }
        wb = types.Washbook(**data)
        assert wb.customer.first_name == "Alice"
        assert wb.recurring_info.current_billable_amount == 29.99
        assert len(wb.tags) == 1
        assert wb.tags[0].number == "T001"
        assert wb.vehicles[0].plate == "ABC123"

    def test_recurring_with_statuses_and_billings(self):
        """Recurring should parse nested recurringStatuses and recurringBillings."""
        data = {
            "id": "rec-001",
            "isOnTrial": False,
            "trialAmount": 0.0,
            "billingSiteCode": "MAIN",
            "creationSiteCode": "MAIN",
            "nextBillDate": "2024-07-01",
            "tags": [],
            "vehicles": [],
            "isSuspended": False,
            "currentRecurringStatusName": "Active",
            "planName": "Unlimited Wash",
            "customer": {"id": "cust-200"},
            "recurringStatuses": [
                {"status": "Active", "date": "2024-01-01"},
                {"status": "Suspended", "date": "2024-03-15"},
            ],
            "recurringBillings": [
                {
                    "amountCharged": 29.99,
                    "date": "2024-06-01",
                    "lastFourCC": "1234",
                    "creditCardExpirationDate": "12/25",
                }
            ],
        }
        rec = types.Recurring(**data)
        assert rec.plan_name == "Unlimited Wash"
        assert len(rec.recurring_statuses) == 2
        assert rec.recurring_statuses[1].status == "Suspended"
        assert len(rec.recurring_billings) == 1
        assert rec.recurring_billings[0].last_four_cc == "1234"

    def test_washbook_list_item(self):
        """WashbookListItem should parse basic list data."""
        data = {
            "id": "wb-100",
            "name": "Basic Plan",
            "balance": "0.00",
            "signUpDate": "2024-01-01",
            "billingSiteId": 1,
            "status": "Active",
        }
        obj = types.WashbookListItem(**data)
        assert obj.sign_up_date == "2024-01-01"
        assert obj.billing_site_id == 1
        assert obj.cancel_date is None


class TestRecurringStatusChange:
    """Tests for RecurringStatusChange (snake_case API, no alias_generator)."""

    def test_parses_snake_case_fields(self):
        """RecurringStatusChange should parse snake_case keys (no camelCase)."""
        data = {
            "washbook_account_id": "wb-500",
            "recurring_id": "rec-500",
            "old_status": "Active",
            "new_status": "Cancelled",
            "status_date": "2024-06-01",
            "employee_name": "Admin",
            "site_code": "MAIN",
        }
        obj = types.RecurringStatusChange(**data)
        assert obj.washbook_account_id == "wb-500"
        assert obj.new_status == "Cancelled"

    def test_does_not_use_camel_case_aliases(self):
        """RecurringStatusChange should NOT produce camelCase aliases."""
        data = {
            "washbook_account_id": "wb-500",
            "recurring_id": "rec-500",
            "old_status": "Active",
            "new_status": "Cancelled",
            "status_date": "2024-06-01",
            "employee_name": "Admin",
            "site_code": "MAIN",
        }
        obj = types.RecurringStatusChange(**data)
        dumped = obj.model_dump(by_alias=True)
        assert "washbook_account_id" in dumped
        assert "washbookAccountId" not in dumped


class TestSiteModel:
    """Tests for Site model with siteID alias override."""

    def test_site_parses_site_id_alias(self):
        """Site should parse siteID from the API response."""
        data = {"siteID": 1, "code": "MAIN", "name": "Main Site"}
        site = types.Site(**data)
        assert site.site_id == 1
        assert site.name == "Main Site"
        assert site.code == "MAIN"

    def test_site_serializes_with_site_id_alias(self):
        """Site.model_dump(by_alias=True) should produce siteID, not siteId."""
        site = types.Site(site_id=1, name="Main Site")
        dumped = site.model_dump(by_alias=True)
        assert "siteID" in dumped
        assert "siteId" not in dumped

    def test_site_nullable_fields(self):
        """Site should allow nullable code and timezone."""
        data = {"siteID": 2, "name": "Remote Site"}
        site = types.Site(**data)
        assert site.code is None
        assert site.timezone is None


class TestRecurringBilling:
    """Tests for RecurringBilling with lastFourCC alias override."""

    def test_last_four_cc_alias(self):
        """RecurringBilling should parse lastFourCC from the API."""
        data = {
            "amountCharged": 19.99,
            "date": "2024-05-01",
            "lastFourCC": "5678",
        }
        billing = types.RecurringBilling(**data)
        assert billing.last_four_cc == "5678"
        dumped = billing.model_dump(by_alias=True)
        assert "lastFourCC" in dumped
        assert dumped["lastFourCC"] == "5678"

    def test_recurring_billing_nullable_expiration(self):
        """RecurringBilling should allow nullable credit card expiration."""
        data = {
            "amountCharged": 10.0,
            "date": "2024-01-01",
            "lastFourCC": "0000",
        }
        billing = types.RecurringBilling(**data)
        assert billing.credit_card_expiration_date is None


class TestEmployeeModels:
    """Tests for Employee-related models."""

    def test_employee_from_camel_case(self):
        """Employee should parse camelCase data."""
        data = {
            "employeeId": 42,
            "firstName": "Bob",
            "lastName": "Builder",
            "active": True,
            "startDate": "2023-01-15",
            "startDateChange": "2023-01-15",
            "phone": "555-0042",
            "email": "bob@example.com",
        }
        emp = types.Employee(**data)
        assert emp.employee_id == 42
        assert emp.first_name == "Bob"
        assert emp.active is True

    def test_employee_list_item(self):
        """EmployeeListItem should parse basic data."""
        data = {"firstName": "Jane", "lastName": "Doe", "employeeId": 7}
        obj = types.EmployeeListItem(**data)
        assert obj.employee_id == 7
        assert obj.last_name == "Doe"

    def test_clock_entry(self):
        """ClockEntry should parse all fields including nullable ones."""
        data = {
            "clockIn": "2024-06-15T08:00:00",
            "clockOut": "2024-06-15T16:00:00",
            "regularRate": 15.0,
            "regularHours": 8.0,
            "overtimeEligible": True,
            "overtimeRate": 22.5,
            "overtimeHours": 0.0,
            "wasModified": False,
            "wasCreatedInBackOffice": False,
            "siteCode": "MAIN",
        }
        entry = types.ClockEntry(**data)
        assert entry.clock_in == "2024-06-15T08:00:00"
        assert entry.regular_rate == 15.0
        assert entry.overtime_eligible is True
        assert entry.modification_timestamp is None
        assert entry.was_created_in_back_office is False


class TestAllExports:
    """Tests for the __all__ export list completeness."""

    def test_all_has_34_models(self):
        """__all__ should contain exactly 34 model names."""
        assert len(types.__all__) == 34

    def test_all_models_are_importable(self):
        """Every name in __all__ should be importable from the types module."""
        for name in types.__all__:
            assert hasattr(types, name), f"{name} not found in types module"
