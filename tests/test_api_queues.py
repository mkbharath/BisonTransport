"""Test HITL Queue and email endpoints."""

import httpx
import pytest
from conftest import API_BASE, auth_headers


class TestHITLQueue:
    def test_list_hitl_queue(self, agent_token):
        res = httpx.get(f"{API_BASE}/queues/hitl", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert "total_count" in data

    def test_approve_order(self, agent_token):
        # First get a pending_review order
        res = httpx.get(f"{API_BASE}/queues/hitl", headers=auth_headers(agent_token))
        data = res.json()
        if data["data"]:
            order_id = data["data"][0]["id"]
            res = httpx.post(f"{API_BASE}/orders/{order_id}/approve", json={}, headers=auth_headers(agent_token))
            assert res.status_code == 200
            assert res.json()["status"] == "order_created"
        else:
            pytest.skip("No orders in HITL queue to approve")

    def test_reject_order(self, agent_token):
        res = httpx.get(f"{API_BASE}/queues/hitl", headers=auth_headers(agent_token))
        data = res.json()
        if data["data"]:
            order_id = data["data"][0]["id"]
            res = httpx.post(
                f"{API_BASE}/orders/{order_id}/reject",
                json={"comments": "Test rejection"},
                headers=auth_headers(agent_token),
            )
            assert res.status_code == 200
        else:
            pytest.skip("No orders in HITL queue to reject")


class TestEmails:
    def test_list_emails(self, agent_token):
        res = httpx.get(f"{API_BASE}/emails", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data

    def test_email_detail(self, agent_token):
        res = httpx.get(f"{API_BASE}/emails", headers=auth_headers(agent_token))
        data = res.json()
        if data["data"]:
            email_id = data["data"][0]["id"]
            res = httpx.get(f"{API_BASE}/emails/{email_id}", headers=auth_headers(agent_token))
            assert res.status_code == 200
            detail = res.json()
            assert "from_address" in detail
            assert "subject" in detail
        else:
            pytest.skip("No emails in DB")


class TestCustomers:
    def test_list_customers(self, agent_token):
        res = httpx.get(f"{API_BASE}/customers", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert data["total_count"] > 0  # Seed customers exist

    def test_search_customers(self, agent_token):
        res = httpx.get(f"{API_BASE}/customers?search=Maple", headers=auth_headers(agent_token))
        assert res.status_code == 200
