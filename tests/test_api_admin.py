"""Test Admin API endpoints: field configs, business rules, email templates."""

import httpx
import pytest
from conftest import API_BASE, auth_headers


class TestFieldConfigs:
    config_id = None

    def test_list_field_configs(self, admin_token):
        res = httpx.get(f"{API_BASE}/admin/field-configs", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert len(data["data"]) > 0  # Seed data exists

    def test_create_field_config(self, admin_token):
        payload = {
            "field_name": "test_api_field",
            "label": "Test API Field",
            "is_mandatory": True,
            "is_conditional": False,
            "display_order": 99,
            "active": True,
        }
        res = httpx.post(f"{API_BASE}/admin/field-configs", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["field_name"] == "test_api_field"
        assert data["is_mandatory"] == True
        TestFieldConfigs.config_id = data["id"]

    def test_update_field_config(self, admin_token):
        if not TestFieldConfigs.config_id:
            pytest.skip("No config created")
        payload = {
            "field_name": "test_api_field",
            "label": "Updated API Field",
            "is_mandatory": False,
            "is_conditional": True,
            "conditional_depends_on": "equipment_type",
            "conditional_value": "reefer",
            "display_order": 99,
            "active": True,
        }
        res = httpx.patch(
            f"{API_BASE}/admin/field-configs/{TestFieldConfigs.config_id}",
            json=payload,
            headers=auth_headers(admin_token),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["label"] == "Updated API Field"
        assert data["is_mandatory"] == False
        assert data["is_conditional"] == True

    def test_active_field_configs_accessible_by_agent(self, agent_token):
        res = httpx.get(f"{API_BASE}/admin/field-configs/active", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data

    def test_delete_field_config(self, admin_token):
        if not TestFieldConfigs.config_id:
            pytest.skip("No config created")
        res = httpx.delete(
            f"{API_BASE}/admin/field-configs/{TestFieldConfigs.config_id}",
            headers=auth_headers(admin_token),
        )
        assert res.status_code == 204


class TestBusinessRules:
    rule_id = None

    def test_list_business_rules(self, admin_token):
        res = httpx.get(f"{API_BASE}/admin/business-rules", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert len(data["data"]) > 0

    def test_create_business_rule(self, admin_token):
        payload = {
            "rule_name": "test_api_rule",
            "field_name": "total_weight",
            "rule_type": "regex_match",
            "rule_expression": "^[0-9]+$",
            "error_message": "Weight must be numeric",
            "severity": "error",
            "priority": 99,
            "active": True,
        }
        res = httpx.post(f"{API_BASE}/admin/business-rules", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["rule_name"] == "test_api_rule"
        TestBusinessRules.rule_id = data["id"]

    def test_delete_business_rule(self, admin_token):
        if not TestBusinessRules.rule_id:
            pytest.skip("No rule created")
        res = httpx.delete(f"{API_BASE}/admin/business-rules/{TestBusinessRules.rule_id}", headers=auth_headers(admin_token))
        assert res.status_code == 204


class TestEmailTemplates:
    template_id = None

    def test_list_templates(self, admin_token):
        res = httpx.get(f"{API_BASE}/admin/email-templates", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data

    def test_create_template(self, admin_token):
        payload = {
            "template_type": "missing_info",
            "name": "Test Template",
            "subject_template": "Test Subject {{order_number}}",
            "body_html_template": "<p>Test body</p>",
            "body_text_template": "Test body",
            "variables": ["order_number"],
            "active": True,
        }
        res = httpx.post(f"{API_BASE}/admin/email-templates", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Test Template"
        TestEmailTemplates.template_id = data["id"]

    def test_delete_template(self, admin_token):
        if not TestEmailTemplates.template_id:
            pytest.skip("No template created")
        res = httpx.delete(f"{API_BASE}/admin/email-templates/{TestEmailTemplates.template_id}", headers=auth_headers(admin_token))
        assert res.status_code == 204
