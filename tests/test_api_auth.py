"""Test authentication and RBAC."""

import httpx
import pytest
from conftest import API_BASE, auth_headers


class TestAuth:
    def test_login_valid_credentials(self):
        res = httpx.post(f"{API_BASE}/auth/login", json={"email": "agent@test.com", "password": "agent123"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        res = httpx.post(f"{API_BASE}/auth/login", json={"email": "wrong@test.com", "password": "wrong"})
        assert res.status_code == 401

    def test_protected_endpoint_without_token(self):
        res = httpx.get(f"{API_BASE}/orders")
        assert res.status_code in (401, 403)

    def test_protected_endpoint_with_token(self, agent_token):
        res = httpx.get(f"{API_BASE}/orders", headers=auth_headers(agent_token))
        assert res.status_code == 200

    def test_admin_endpoint_with_agent_token(self, agent_token):
        res = httpx.get(f"{API_BASE}/admin/field-configs", headers=auth_headers(agent_token))
        assert res.status_code == 403

    def test_admin_endpoint_with_admin_token(self, admin_token):
        res = httpx.get(f"{API_BASE}/admin/field-configs", headers=auth_headers(admin_token))
        assert res.status_code == 200

    def test_health_endpoint_no_auth(self):
        res = httpx.get(f"{API_BASE}/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("healthy", "degraded")
