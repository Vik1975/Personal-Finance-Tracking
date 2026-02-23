"""Simplified tests for export functionality."""

from fastapi.testclient import TestClient

from app.main import app


class TestExportEndpoints:
    """Test export endpoints are registered and accessible."""

    def test_export_csv_endpoint_exists(self):
        """Test CSV export endpoint is registered."""
        client = TestClient(app)
        response = client.get("/export/transactions/csv")
        # Should return 401 (unauthorized) not 404 (not found)
        assert response.status_code == 401

    def test_export_excel_endpoint_exists(self):
        """Test Excel export endpoint is registered."""
        client = TestClient(app)
        response = client.get("/export/transactions/excel")
        assert response.status_code == 401

    def test_export_analytics_endpoint_exists(self):
        """Test Analytics export endpoint is registered."""
        client = TestClient(app)
        response = client.get("/export/analytics/excel")
        assert response.status_code == 401

    def test_export_requires_authentication(self):
        """Test all export endpoints require authentication."""
        client = TestClient(app)

        endpoints = [
            "/export/transactions/csv",
            "/export/transactions/excel",
            "/export/analytics/excel",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"
            assert "Not authenticated" in response.json()["detail"]
