"""Health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Health API tests."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health endpoint should return success."""
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["status"] == "healthy"
