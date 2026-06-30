"""Test reporting and dashboard endpoints."""

import httpx
import pytest
from conftest import API_BASE, auth_headers


class TestDashboard:
    def test_dashboard_returns_all_kpis(self, agent_token):
        res = httpx.get(f"{API_BASE}/reports/dashboard", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        required_keys = [
            "total_orders", "pending", "awaiting_customer", "auto_processed",
            "stp_rate", "hitl_queue_depth", "completed", "failed",
            "avg_e2e_time", "extraction_accuracy",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["stp_rate"], (int, float))

    def test_stp_trend_7_days(self, agent_token):
        res = httpx.get(f"{API_BASE}/reports/stp-trend?days=7", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert data["days"] == 7
        # Should have ~7-8 data points
        assert len(data["data"]) >= 7
        for point in data["data"]:
            assert "date" in point
            assert "stp_rate" in point
            assert 0 <= point["stp_rate"] <= 100

    def test_stp_trend_30_days(self, agent_token):
        res = httpx.get(f"{API_BASE}/reports/stp-trend?days=30", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert len(data["data"]) >= 30


class TestAuditLogs:
    def test_list_audit_logs(self, agent_token):
        res = httpx.get(f"{API_BASE}/admin/audit-logs", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert "total_count" in data

    def test_audit_logs_with_search(self, agent_token):
        res = httpx.get(f"{API_BASE}/admin/audit-logs?search=order", headers=auth_headers(agent_token))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
