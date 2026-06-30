"""Shared fixtures for integration tests.

These tests run against the live Docker services.
Requires: docker compose up -d (all services running)
"""

import os
import pytest
import httpx

API_BASE = os.environ.get("API_BASE", "http://localhost:8000/api/v1")


@pytest.fixture(scope="session")
def api_base():
    return API_BASE


@pytest.fixture(scope="session")
def agent_token():
    """Get JWT token for agent user."""
    res = httpx.post(f"{API_BASE}/auth/login", json={"email": "agent@test.com", "password": "agent123"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token():
    """Get JWT token for admin user."""
    res = httpx.post(f"{API_BASE}/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def supervisor_token():
    """Get JWT token for supervisor user."""
    res = httpx.post(f"{API_BASE}/auth/login", json={"email": "supervisor@test.com", "password": "super123"})
    assert res.status_code == 200, f"Supervisor login failed: {res.text}"
    return res.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
