"""Test Order CRUD API endpoints."""

import httpx
import pytest
from conftest import API_BASE, auth_headers


class TestOrderCRUD:
    order_id = None

    def test_create_order(self, agent_token):
        payload = {
            "customer_name": "API Test Corp",
            "contact_name": "Test User",
            "contact_email": "apitest@example.com",
            "contact_phone": "+1234567890",
            "pickup_location_name": "Test Warehouse",
            "pickup_address": {"line1": "100 Test St", "city": "TestCity", "state": "TX", "postal_code": "75001", "country": "US"},
            "pickup_date": "2026-08-15",
            "delivery_location_name": "Test Destination",
            "delivery_address": {"line1": "200 Dest Ave", "city": "DestCity", "state": "CA", "postal_code": "90001", "country": "US"},
            "delivery_date": "2026-08-17",
            "commodity": "Test Electronics",
            "freight_type": "ftl",
            "equipment_type": "dry_van",
            "total_weight": 15000.0,
            "weight_unit": "lbs",
            "num_pallets": 10,
            "hazmat_indicator": False,
        }
        res = httpx.post(f"{API_BASE}/orders", json=payload, headers=auth_headers(agent_token))
        assert res.status_code == 201, f"Create failed: {res.text}"
        data = res.json()
        assert "order_number" in data
        assert data["customer_name"] == "API Test Corp"
        assert data["status"] == "order_created"
        TestOrderCRUD.order_id = data["id"]

    def test_list_orders(self, agent_token):
        res = httpx.get(f"{API_BASE}/orders", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert "total_count" in data
        assert "total_pages" in data
        assert data["total_count"] > 0

    def test_get_order_detail(self, agent_token):
        if not TestOrderCRUD.order_id:
            pytest.skip("No order created")
        res = httpx.get(f"{API_BASE}/orders/{TestOrderCRUD.order_id}", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert data["customer_name"] == "API Test Corp"
        assert data["commodity"] == "Test Electronics"
        assert data["pickup_date"] == "2026-08-15"

    def test_update_order(self, agent_token):
        if not TestOrderCRUD.order_id:
            pytest.skip("No order created")
        res = httpx.patch(
            f"{API_BASE}/orders/{TestOrderCRUD.order_id}",
            json={"customer_name": "Updated Corp Name", "commodity": "Updated Goods"},
            headers=auth_headers(agent_token),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["customer_name"] == "Updated Corp Name"
        assert data["commodity"] == "Updated Goods"

    def test_filter_orders_by_status(self, agent_token):
        res = httpx.get(f"{API_BASE}/orders?status=order_created", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        for order in data["data"]:
            assert order["status"] == "order_created"

    def test_clone_order(self, agent_token):
        if not TestOrderCRUD.order_id:
            pytest.skip("No order created")
        res = httpx.post(f"{API_BASE}/orders/{TestOrderCRUD.order_id}/clone", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert data["id"] != TestOrderCRUD.order_id
        assert "ORD-" in data["order_number"]

    def test_get_order_history(self, agent_token):
        if not TestOrderCRUD.order_id:
            pytest.skip("No order created")
        res = httpx.get(f"{API_BASE}/orders/{TestOrderCRUD.order_id}/history", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data

    def test_delete_order_requires_supervisor(self, agent_token):
        if not TestOrderCRUD.order_id:
            pytest.skip("No order created")
        res = httpx.delete(f"{API_BASE}/orders/{TestOrderCRUD.order_id}", headers=auth_headers(agent_token))
        assert res.status_code == 403  # Agent can't delete

    def test_delete_order_as_supervisor(self, supervisor_token):
        if not TestOrderCRUD.order_id:
            pytest.skip("No order created")
        res = httpx.delete(f"{API_BASE}/orders/{TestOrderCRUD.order_id}", headers=auth_headers(supervisor_token))
        assert res.status_code == 204
