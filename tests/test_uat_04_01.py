"""UAT tests for 04-01: Transaction & Customer Models."""

import json

from sonnys_data_client.types._base import SonnysModel
from sonnys_data_client.types._transactions import (
    Transaction,
    TransactionDiscount,
    TransactionItem,
    TransactionJobItem,
    TransactionListItem,
    TransactionTender,
    TransactionV2ListItem,
)
from sonnys_data_client.types._customers import (
    Address,
    Customer,
    CustomerListItem,
)


# --- Test 1: camelCase alias generation ---

class TestCamelCaseAliases:
    def test_snake_case_fields_produce_camel_case_json(self):
        t = TransactionTender(
            tender="Cash", amount=10.0, change=0.0, total=10.0,
            credit_card_last_four="1234",
        )
        data = json.loads(t.model_dump_json(by_alias=True))
        assert "creditCardLastFour" in data
        assert "tenderSubType" in data
        assert data["creditCardLastFour"] == "1234"

    def test_populate_by_name_allows_snake_case_construction(self):
        t = TransactionTender(
            tender="Credit", amount=5.0, change=0.0, total=5.0,
        )
        assert t.tender == "Credit"
        assert t.amount == 5.0

    def test_populate_by_alias_allows_camel_case_construction(self):
        t = TransactionTender(
            **{"tender": "Debit", "amount": 7.0, "change": 0.0, "total": 7.0,
               "creditCardLastFour": "5678"}
        )
        assert t.credit_card_last_four == "5678"


# --- Test 2: Transaction sub-models ---

class TestTransactionSubModels:
    def test_transaction_tender_all_fields(self):
        t = TransactionTender(
            tender="Credit", tender_sub_type="Visa",
            amount=25.99, change=0.0, total=25.99,
            reference_number="REF123",
            credit_card_last_four="4242",
            credit_card_expiration_date="12/25",
        )
        assert t.tender_sub_type == "Visa"
        assert t.reference_number == "REF123"

    def test_transaction_tender_nullable_defaults(self):
        t = TransactionTender(tender="Cash", amount=10.0, change=0.0, total=10.0)
        assert t.tender_sub_type is None
        assert t.reference_number is None
        assert t.credit_card_last_four is None

    def test_transaction_item_all_fields(self):
        item = TransactionItem(
            name="Full Service", sku="FS001", department="Wash",
            quantity=1, gross=15.0, net=14.0, discount=1.0,
            tax=0.98, additional_fee=0.0, is_voided=False,
        )
        assert item.name == "Full Service"
        assert item.is_voided is False

    def test_transaction_discount_all_fields(self):
        d = TransactionDiscount(
            discount_name="10% Off", discount_sku="D10",
            applied_to_item_name="Full Service",
            discount=1.50, discount_code="SAVE10",
        )
        assert d.discount_name == "10% Off"
        assert d.discount == 1.50


# --- Test 3: Transaction main models ---

class TestTransactionMainModels:
    def test_transaction_list_item(self):
        t = TransactionListItem(
            trans_number=1001, trans_id="abc-123", total=25.99, date="2024-01-15",
        )
        data = json.loads(t.model_dump_json(by_alias=True))
        assert data["transNumber"] == 1001
        assert data["transId"] == "abc-123"

    def test_transaction_v2_extends_list_item(self):
        t = TransactionV2ListItem(
            trans_number=1001, trans_id="abc-123", total=25.99, date="2024-01-15",
            is_recurring_plan_sale=False, is_recurring_plan_redemption=True,
            transaction_status="Completed",
        )
        assert t.trans_number == 1001  # inherited
        assert t.transaction_status == "Completed"  # v2 field
        assert isinstance(t, TransactionListItem)

    def test_transaction_full_detail_with_nested(self):
        t = Transaction(
            id="1:2", number=1001, type="Sale",
            complete_date="2024-01-15T10:30:00",
            location_code="MAIN", sales_device_name="POS1",
            total=25.99,
            tenders=[
                {"tender": "Credit", "tenderSubType": "Visa",
                 "amount": 25.99, "change": 0.0, "total": 25.99},
            ],
            items=[
                {"name": "Full Service", "department": "Wash",
                 "quantity": 1, "gross": 25.99, "net": 24.99,
                 "discount": 1.0, "tax": 1.82, "additionalFee": 0.0,
                 "isVoided": False},
            ],
            discount=[],
            is_recurring_payment=False, is_recurring_redemption=False,
            is_recurring_sale=False, is_prepaid_redemption=False,
            is_prepaid_sale=False,
        )
        assert len(t.tenders) == 1
        assert isinstance(t.tenders[0], TransactionTender)
        assert t.tenders[0].tender_sub_type == "Visa"
        assert len(t.items) == 1
        assert isinstance(t.items[0], TransactionItem)

    def test_transaction_nullable_fields(self):
        t = Transaction(
            id="1:2", number=1, type="Sale",
            complete_date="2024-01-15", location_code="MAIN",
            sales_device_name="POS1", total=10.0,
            tenders=[], items=[], discount=[],
            is_recurring_payment=False, is_recurring_redemption=False,
            is_recurring_sale=False, is_prepaid_redemption=False,
            is_prepaid_sale=False,
        )
        assert t.customer_name is None
        assert t.customer_id is None
        assert t.vehicle_license_plate is None

    def test_transaction_json_roundtrip(self):
        t = Transaction(
            id="1:2", number=1, type="Sale",
            complete_date="2024-01-15", location_code="MAIN",
            sales_device_name="POS1", total=10.0,
            tenders=[], items=[], discount=[],
            is_recurring_payment=False, is_recurring_redemption=False,
            is_recurring_sale=False, is_prepaid_redemption=False,
            is_prepaid_sale=False,
        )
        data = json.loads(t.model_dump_json(by_alias=True))
        assert "salesDeviceName" in data
        assert "completeDate" in data
        assert "isRecurringPayment" in data
        # Roundtrip: parse camelCase JSON back into model
        t2 = Transaction.model_validate(data)
        assert t2.sales_device_name == "POS1"

    def test_transaction_job_item_extends_transaction(self):
        t = TransactionJobItem(
            id="1:2", number=1, type="Sale",
            complete_date="2024-01-15", location_code="MAIN",
            sales_device_name="POS1", total=10.0,
            tenders=[], items=[], discount=[],
            is_recurring_payment=False, is_recurring_redemption=False,
            is_recurring_sale=False, is_prepaid_redemption=False,
            is_prepaid_sale=False,
            is_recurring_plan_sale=True,
            is_recurring_plan_redemption=False,
            transaction_status="Completed",
        )
        assert isinstance(t, Transaction)
        assert t.is_recurring_plan_sale is True
        assert t.transaction_status == "Completed"


# --- Test 4: Customer models ---

class TestCustomerModels:
    def test_address_all_nullable(self):
        a = Address()
        assert a.address1 is None
        assert a.city is None
        assert a.postal_code is None

    def test_address_with_values(self):
        a = Address(
            address1="123 Main St", city="Springfield",
            state="IL", postal_code="62701",
        )
        data = json.loads(a.model_dump_json(by_alias=True))
        assert data["postalCode"] == "62701"

    def test_customer_list_item(self):
        c = CustomerListItem(
            customer_id="cust-001", first_name="John", last_name="Doe",
            is_active=True, created_date="2024-01-01", modified_date="2024-06-15",
        )
        data = json.loads(c.model_dump_json(by_alias=True))
        assert data["customerId"] == "cust-001"
        assert data["firstName"] == "John"

    def test_customer_detail_with_nested_address(self):
        c = Customer(
            id="1:2", number="001",
            first_name="Jane", last_name="Smith",
            company_name="Acme Corp", loyalty_number="LYL-999",
            address={"address1": "456 Oak Ave", "city": "Portland", "state": "OR"},
            phone="555-0100", email="jane@acme.com",
            is_active=True, allow_sms=True, modify_date="2024-06-15",
        )
        assert isinstance(c.address, Address)
        assert c.address.city == "Portland"
        assert c.email == "jane@acme.com"

    def test_customer_nullable_fields(self):
        c = Customer(
            id="1:2", number="001",
            first_name="John", last_name="Doe",
            company_name="", loyalty_number="",
            address=Address(), phone="555-0000",
            is_active=True, allow_sms=False, modify_date="2024-01-01",
        )
        assert c.email is None
        assert c.birth_date is None
        assert c.recurring_sms_signup_date is None

    def test_customer_json_roundtrip(self):
        c = Customer(
            id="1:2", number="001",
            first_name="John", last_name="Doe",
            company_name="", loyalty_number="",
            address=Address(city="Denver", state="CO"),
            phone="555-0000",
            is_active=True, allow_sms=False, modify_date="2024-01-01",
        )
        data = json.loads(c.model_dump_json(by_alias=True))
        assert data["firstName"] == "John"
        assert data["address"]["city"] == "Denver"
        # Roundtrip
        c2 = Customer.model_validate(data)
        assert c2.address.state == "CO"
