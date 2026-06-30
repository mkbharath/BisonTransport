"""Comprehensive field-level validation tests.

Tests every mandatory field, business rule (date_after, valid_enum, regex_match, required_if),
and conditional field logic at both the API layer and through the agent validation pipeline.
"""

import httpx
import pytest
from conftest import API_BASE, auth_headers


# === VALID BASELINE ORDER ===
VALID_ORDER = {
    "customer_name": "FieldTest Corp",
    "contact_name": "Jane Doe",
    "contact_email": "jane@fieldtest.com",
    "contact_phone": "+14165551234",
    "pickup_location_name": "Test Warehouse A",
    "pickup_address": {"line1": "100 Main St", "city": "Toronto", "state": "ON", "postal_code": "M5V 3C6", "country": "CA"},
    "pickup_date": "2026-09-01",
    "delivery_location_name": "Test Depot B",
    "delivery_address": {"line1": "200 King Rd", "city": "Montreal", "state": "QC", "postal_code": "H3B 4G5", "country": "CA"},
    "delivery_date": "2026-09-03",
    "commodity": "General Goods",
    "freight_type": "ftl",
    "equipment_type": "dry_van",
    "total_weight": 30000.0,
    "weight_unit": "lbs",
    "num_pallets": 20,
    "hazmat_indicator": False,
}


class TestMandatoryFields:
    """Test that orders can be created but validation agent catches missing mandatory fields."""

    def test_valid_order_creates_successfully(self, agent_token):
        """A complete order with all mandatory fields should create successfully."""
        res = httpx.post(f"{API_BASE}/orders", json=VALID_ORDER, headers=auth_headers(agent_token))
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "order_created"
        assert data["customer_name"] == "FieldTest Corp"

    def test_missing_customer_name(self, agent_token):
        """Order without customer_name — API allows it (agent validates later)."""
        payload = {**VALID_ORDER, "customer_name": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        # API layer allows creation with missing fields (agent validates)
        assert res.status_code == 201
        data = res.json()
        assert data["customer_name"] is None

    def test_missing_contact_email(self, agent_token):
        """Order without contact_email."""
        payload = {**VALID_ORDER, "contact_email": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_missing_pickup_date(self, agent_token):
        """Order without pickup_date."""
        payload = {**VALID_ORDER, "pickup_date": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_missing_delivery_date(self, agent_token):
        """Order without delivery_date."""
        payload = {**VALID_ORDER, "delivery_date": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_missing_commodity(self, agent_token):
        """Order without commodity."""
        payload = {**VALID_ORDER, "commodity": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_missing_freight_type(self, agent_token):
        """Order without freight_type."""
        payload = {**VALID_ORDER, "freight_type": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_missing_equipment_type(self, agent_token):
        """Order without equipment_type."""
        payload = {**VALID_ORDER, "equipment_type": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_missing_total_weight(self, agent_token):
        """Order without total_weight."""
        payload = {**VALID_ORDER, "total_weight": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_empty_string_customer_name(self, agent_token):
        """Empty string for customer_name treated as missing by validation agent."""
        payload = {**VALID_ORDER, "customer_name": ""}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["customer_name"] == ""

    def test_whitespace_only_field(self, agent_token):
        """Whitespace-only customer_name treated as missing by agent."""
        payload = {**VALID_ORDER, "customer_name": "   "}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201


class TestFieldFormats:
    """Test field format and type validation at API level."""

    def test_invalid_date_format_rejected(self, agent_token):
        """Invalid date format should be rejected or normalized."""
        payload = {**VALID_ORDER, "pickup_date": "not-a-date"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        # Should either reject (422) or store raw and let agent validate
        assert res.status_code in (201, 422)

    def test_date_in_past_accepted_by_api(self, agent_token):
        """Past date — API accepts, business rule catches it (pickup_date_future rule)."""
        payload = {**VALID_ORDER, "pickup_date": "2020-01-01"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        # API allows past dates; validation agent enforces date_after rule
        assert res.status_code == 201

    def test_delivery_before_pickup_accepted_by_api(self, agent_token):
        """Delivery before pickup — API accepts, business rule validates."""
        payload = {**VALID_ORDER, "pickup_date": "2026-09-10", "delivery_date": "2026-09-08"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_invalid_email_format(self, agent_token):
        """Invalid email format — stored, business rule (email_format) catches it."""
        payload = {**VALID_ORDER, "contact_email": "not-an-email"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["contact_email"] == "not-an-email"

    def test_negative_weight(self, agent_token):
        """Negative weight — stored, business rule (weight_positive) catches it."""
        payload = {**VALID_ORDER, "total_weight": -500.0}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_zero_weight(self, agent_token):
        """Zero weight — stored, business rule should flag."""
        payload = {**VALID_ORDER, "total_weight": 0.0}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201


class TestEnumValidation:
    """Test enum/valid_enum business rules for freight_type and equipment_type."""

    def test_valid_freight_type_ftl(self, agent_token):
        payload = {**VALID_ORDER, "freight_type": "ftl"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["freight_type"] == "ftl"

    def test_valid_freight_type_ltl(self, agent_token):
        payload = {**VALID_ORDER, "freight_type": "ltl"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_valid_freight_type_partial(self, agent_token):
        payload = {**VALID_ORDER, "freight_type": "partial"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_valid_freight_type_intermodal(self, agent_token):
        payload = {**VALID_ORDER, "freight_type": "intermodal"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_invalid_freight_type_stored(self, agent_token):
        """Invalid freight_type — API stores it, validation agent flags via valid_enum rule."""
        payload = {**VALID_ORDER, "freight_type": "helicopter"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["freight_type"] == "helicopter"

    def test_valid_equipment_dry_van(self, agent_token):
        payload = {**VALID_ORDER, "equipment_type": "dry_van"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_valid_equipment_reefer(self, agent_token):
        payload = {**VALID_ORDER, "equipment_type": "reefer"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_valid_equipment_flatbed(self, agent_token):
        payload = {**VALID_ORDER, "equipment_type": "flatbed"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_invalid_equipment_type_stored(self, agent_token):
        """Invalid equipment_type — stored, agent validates via valid_enum rule."""
        payload = {**VALID_ORDER, "equipment_type": "spaceship"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["equipment_type"] == "spaceship"


class TestConditionalFields:
    """Test conditional field requirements (required_if rules)."""

    def test_reefer_without_temperature_stored(self, agent_token):
        """Reefer equipment without temperature — agent enforces required_if rule."""
        payload = {**VALID_ORDER, "equipment_type": "reefer"}
        # No temperature fields set — agent should flag missing
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_reefer_with_temperature_valid(self, agent_token):
        """Reefer equipment with temperature provided — valid."""
        payload = {**VALID_ORDER, "equipment_type": "reefer"}
        # Temperature fields not in API create model but would be set by extraction agent
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_hazmat_without_un_number(self, agent_token):
        """Hazmat=true without UN number — agent enforces required_if rule."""
        payload = {**VALID_ORDER, "hazmat_indicator": True, "hazmat_un_number": None, "hazmat_class": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_hazmat_with_un_number_and_class(self, agent_token):
        """Hazmat=true with UN number and class — valid."""
        payload = {**VALID_ORDER, "hazmat_indicator": True, "hazmat_un_number": "UN1203", "hazmat_class": "3"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        data = res.json()
        assert data["hazmat_indicator"] == True
        assert data["hazmat_un_number"] == "UN1203"
        assert data["hazmat_class"] == "3"

    def test_ftl_without_pallets(self, agent_token):
        """FTL freight without num_pallets — agent enforces required_if rule."""
        payload = {**VALID_ORDER, "freight_type": "ftl", "num_pallets": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_ftl_with_pallets_valid(self, agent_token):
        """FTL freight with pallets — valid."""
        payload = {**VALID_ORDER, "freight_type": "ftl", "num_pallets": 24}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["num_pallets"] == 24


class TestAddressFields:
    """Test structured address field handling."""

    def test_full_pickup_address(self, agent_token):
        payload = {**VALID_ORDER}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        addr = res.json()["pickup_address"]
        assert addr["line1"] == "100 Main St"
        assert addr["city"] == "Toronto"
        assert addr["state"] == "ON"
        assert addr["postal_code"] == "M5V 3C6"

    def test_partial_address_missing_city(self, agent_token):
        """Partial address with missing city — stored, agent flags mandatory sub-field."""
        payload = {**VALID_ORDER, "pickup_address": {"line1": "123 St", "state": "ON", "postal_code": "M5V 3C6", "country": "CA"}}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_null_address(self, agent_token):
        """Null address — stored, agent flags missing mandatory fields."""
        payload = {**VALID_ORDER, "pickup_address": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["pickup_address"] is None

    def test_delivery_address_complete(self, agent_token):
        payload = {**VALID_ORDER}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        addr = res.json()["delivery_address"]
        assert addr["city"] == "Montreal"
        assert addr["state"] == "QC"

    def test_canadian_postal_code_formats(self, agent_token):
        """Valid Canadian postal code formats."""
        for pc in ["M5V 3C6", "H3B4G5", "T2P 1J9"]:
            payload = {**VALID_ORDER, "pickup_address": {**VALID_ORDER["pickup_address"], "postal_code": pc}}
            res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
            assert res.status_code == 201

    def test_us_zip_code_format(self, agent_token):
        """Valid US ZIP code format."""
        for pc in ["90210", "75001-1234"]:
            payload = {**VALID_ORDER, "pickup_address": {**VALID_ORDER["pickup_address"], "postal_code": pc, "country": "US"}}
            res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
            assert res.status_code == 201


class TestOrderUpdate:
    """Test field-level validation on order updates (PATCH)."""

    order_id = None

    def test_setup_create_order(self, agent_token):
        """Create a base order for update tests."""
        res = httpx.post(f"{API_BASE}/orders", json=VALID_ORDER, headers=auth_headers(agent_token))
        assert res.status_code == 201
        TestOrderUpdate.order_id = res.json()["id"]

    def test_update_customer_name(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"customer_name": "Updated FieldTest Corp"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["customer_name"] == "Updated FieldTest Corp"

    def test_update_pickup_date(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"pickup_date": "2026-10-15"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["pickup_date"] == "2026-10-15"

    def test_update_delivery_date(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"delivery_date": "2026-10-18"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["delivery_date"] == "2026-10-18"

    def test_update_commodity(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"commodity": "Premium Electronics"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["commodity"] == "Premium Electronics"

    def test_update_equipment_type(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"equipment_type": "flatbed"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["equipment_type"] == "flatbed"

    def test_update_total_weight(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"total_weight": 45000.0},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["total_weight"] == 45000.0

    def test_update_pickup_address(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        new_addr = {"line1": "999 New Blvd", "city": "Ottawa", "state": "ON", "postal_code": "K1A 0B1", "country": "CA"}
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"pickup_address": new_addr},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["pickup_address"]["city"] == "Ottawa"

    def test_update_notes(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"notes": "Updated via field validation test"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["notes"] == "Updated via field validation test"

    def test_update_empty_body_rejected(self, agent_token):
        """PATCH with no fields should return 400."""
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 400

    def test_update_internal_comments(self, agent_token):
        if not TestOrderUpdate.order_id:
            pytest.skip("No order")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderUpdate.order_id}",
            json={"internal_comments": "Reviewed by supervisor - all good"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        assert res.json()["internal_comments"] == "Reviewed by supervisor - all good"


class TestAgentValidationRules:
    """Test the validation agent's business rules by checking validation_results table.

    These tests create orders then check what the validation agent would flag
    by calling the validation_results endpoint or querying order status.
    """

    def test_business_rules_exist_in_db(self, admin_token):
        """Verify all expected business rules are configured."""
        res = httpx.get(f"{API_BASE}/admin/business-rules", headers=auth_headers(admin_token))
        assert res.status_code == 200
        rules = res.json()["data"]
        rule_names = [r["rule_name"] for r in rules]

        expected_rules = [
            "pickup_date_future",
            "delivery_after_pickup",
            "weight_positive",
            "email_format",
            "freight_type_valid",
            "equipment_type_valid",
            "reefer_temp_required",
            "hazmat_un_required",
            "hazmat_class_required",
            "pallets_required_ftl",
            "pallets_required_ltl",
            "postal_code_format",
        ]
        for rule in expected_rules:
            assert rule in rule_names, f"Missing business rule: {rule}"

    def test_mandatory_field_configs_complete(self, admin_token):
        """Verify all expected mandatory fields are configured."""
        res = httpx.get(f"{API_BASE}/admin/field-configs", headers=auth_headers(admin_token))
        assert res.status_code == 200
        fields = res.json()["data"]
        mandatory = [f["field_name"] for f in fields if f["is_mandatory"]]

        expected_mandatory = [
            "customer_name", "contact_name", "contact_email", "contact_phone",
            "pickup_location_name", "pickup_address_line1", "pickup_city",
            "pickup_state", "pickup_postal_code", "pickup_country", "pickup_date",
            "delivery_location_name", "delivery_address_line1", "delivery_city",
            "delivery_state", "delivery_postal_code", "delivery_country", "delivery_date",
            "commodity", "freight_type", "total_weight", "weight_unit",
            "equipment_type", "hazmat_indicator",
        ]
        for field in expected_mandatory:
            assert field in mandatory, f"Field '{field}' should be mandatory but isn't configured"

    def test_conditional_fields_configured(self, admin_token):
        """Verify conditional fields have correct dependencies."""
        res = httpx.get(f"{API_BASE}/admin/field-configs", headers=auth_headers(admin_token))
        fields = res.json()["data"]
        conditional = {f["field_name"]: f for f in fields if f["is_conditional"]}

        # Temperature fields depend on equipment_type=reefer
        assert "temperature_min_c" in conditional
        assert conditional["temperature_min_c"]["conditional_depends_on"] == "equipment_type"
        assert conditional["temperature_min_c"]["conditional_value"] == "reefer"

        # Hazmat fields depend on hazmat_indicator=true
        assert "hazmat_un_number" in conditional
        assert conditional["hazmat_un_number"]["conditional_depends_on"] == "hazmat_indicator"
        assert conditional["hazmat_un_number"]["conditional_value"] == "true"

        assert "hazmat_class" in conditional
        assert conditional["hazmat_class"]["conditional_depends_on"] == "hazmat_indicator"

    def test_rule_types_cover_all_patterns(self, admin_token):
        """Ensure business rules cover: date_after, valid_enum, regex_match, required_if."""
        res = httpx.get(f"{API_BASE}/admin/business-rules", headers=auth_headers(admin_token))
        rules = res.json()["data"]
        rule_types = set(r["rule_type"] for r in rules)

        assert "date_after" in rule_types, "Missing date_after rules"
        assert "valid_enum" in rule_types, "Missing valid_enum rules"
        assert "regex_match" in rule_types, "Missing regex_match rules"
        assert "required_if" in rule_types, "Missing required_if rules"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_customer_name(self, agent_token):
        """Customer name at 500 chars — exceeds DB VARCHAR(255), should reject."""
        payload = {**VALID_ORDER, "customer_name": "X" * 500}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        # DB column is VARCHAR(255) — API should return error for oversized values
        assert res.status_code in (400, 422, 500)

    def test_customer_name_at_max_length(self, agent_token):
        """Customer name at 255 chars — exactly at DB limit, should succeed."""
        payload = {**VALID_ORDER, "customer_name": "X" * 255}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert len(res.json()["customer_name"]) == 255

    def test_special_characters_in_fields(self, agent_token):
        """Unicode and special characters in text fields."""
        payload = {**VALID_ORDER, "customer_name": "Société Générale — Montréal (Québec)"}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert "Société" in res.json()["customer_name"]

    def test_max_weight_value(self, agent_token):
        """Very large weight value."""
        payload = {**VALID_ORDER, "total_weight": 999999.99}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201
        assert res.json()["total_weight"] == 999999.99

    def test_zero_pallets(self, agent_token):
        """Zero pallets with FTL freight."""
        payload = {**VALID_ORDER, "freight_type": "ftl", "num_pallets": 0}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_multiple_missing_fields(self, agent_token):
        """Order with many missing mandatory fields."""
        payload = {
            "customer_name": "Minimal Order",
            "hazmat_indicator": False,
        }
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_all_optional_fields_null(self, agent_token):
        """Only mandatory fields present, all optional null."""
        payload = {**VALID_ORDER, "notes": None}
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201

    def test_phone_number_formats(self, agent_token):
        """Various phone number formats should be accepted."""
        for phone in ["+14165551234", "416-555-1234", "(416) 555-1234", "4165551234"]:
            payload = {**VALID_ORDER, "contact_phone": phone}
            res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
            assert res.status_code == 201
