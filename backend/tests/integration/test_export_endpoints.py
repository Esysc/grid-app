"""
Integration tests for export endpoints in main.py
"""

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta, timezone
from typing import Any

import main
import pytest
from fastapi.testclient import TestClient
from main import app
from pytest import MonkeyPatch

from auth import create_access_token


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate valid JWT auth headers for testing"""
    access_token = create_access_token(data={"sub": "admin"}, expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def mock_s3_exporter(monkeypatch: MonkeyPatch):
    """Mock S3 exporter to avoid network calls during integration tests.

    Replaces `main.s3_exporter` with a fake exporter that returns predictable
    results and never talks to LocalStack/AWS.
    """

    class MockExporter:
        bucket_name = "grid-monitor-exports"

        def ensure_bucket_exists(self):
            return None

        def export_voltage_data(self, data: list[dict[str, Any]], hours: int = 24):
            key = (
                f"exports/voltage_{hours}h_"
                f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
            )
            return {
                "status": "success",
                "message": f"Exported voltage data ({len(data)} records) to {key}",
                "location": f"s3://{self.bucket_name}/{key}",
                "key": key,
            }

        def export_fault_events(self, data: list[dict[str, Any]]):
            key = f"exports/faults_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
            return {
                "status": "success",
                "message": f"Exported fault events ({len(data)} records) to {key}",
                "location": f"s3://{self.bucket_name}/{key}",
                "key": key,
            }

        def list_exports(self) -> dict[str, Any]:
            files: list[dict[str, Any]] = [
                {
                    "key": "exports/voltage_24h_20260111.json",
                    "size": 1024,
                    "last_modified": datetime(
                        2026, 1, 11, 10, 0, 0, tzinfo=timezone.utc
                    ).isoformat(),
                },
                {
                    "key": "exports/faults_20260110.csv",
                    "size": 2048,
                    "last_modified": datetime(
                        2026, 1, 10, 15, 30, 0, tzinfo=timezone.utc
                    ).isoformat(),
                },
            ]
            return {"status": "success", "files": files}

        def generate_presigned_url(self, key: str, expires_in: int = 3600):
            return {
                "status": "success",
                "url": f"https://example.com/download?key={key}&expires={expires_in}",
            }

    monkeypatch.setattr(main, "s3_exporter", MockExporter())


class TestExportEndpoints:
    """Test export and archive functionality"""

    def test_export_voltage_endpoint(self, client: TestClient, auth_headers: dict[str, str]):
        """Test POST /export/voltage endpoint"""
        response = client.post(
            "/export/voltage",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "key" in data
        assert "location" in data
        assert data["key"].startswith("exports/voltage_")

    def test_export_voltage_with_hours_parameter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test voltage export with custom hours parameter"""
        response = client.post(
            "/export/voltage",
            params={"hours": 48},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "voltage_48h_" in data["key"]

    def test_export_faults_endpoint(self, client: TestClient, auth_headers: dict[str, str]):
        """Test POST /export/faults endpoint"""
        response = client.post(
            "/export/faults",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "key" in data
        assert data["key"].startswith("exports/faults_")

    def test_export_faults_with_hours_parameter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test faults export with custom hours parameter"""
        response = client.post(
            "/export/faults",
            params={"hours": 12},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_export_list_endpoint(self, client: TestClient, auth_headers: dict[str, str]):
        """Test GET /export/list endpoint"""
        response = client.get(
            "/export/list",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_get_presigned_url_endpoint(self, client: TestClient, auth_headers: dict[str, str]):
        """Test GET /export/{file_key} endpoint for presigned URL"""
        # First create an export
        export_response = client.post(
            "/export/voltage",
            headers=auth_headers,
        )
        export_data = export_response.json()
        file_key = export_data["key"]

        # Now get presigned URL
        response = client.get(
            f"/export/{file_key}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "url" in data
        assert data["url"].startswith("http")

    def test_export_endpoint_requires_authentication(self, client: TestClient):
        """Test that export endpoints require valid JWT token"""
        response = client.post("/export/voltage")

        assert response.status_code == 401

    def test_list_exports_requires_authentication(self, client: TestClient):
        """Test that list endpoint requires valid JWT token"""
        response = client.get("/export/list")

        assert response.status_code == 401

    def test_presigned_url_requires_authentication(self, client: TestClient):
        """Test that presigned URL endpoint requires valid JWT token"""
        response = client.get("/export/exports/test.json")

        assert response.status_code == 401

    def test_export_voltage_format_parameter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test voltage export with format parameter"""
        response = client.post(
            "/export/voltage",
            params={"format": "csv"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Note: format parameter not implemented yet, defaults to JSON

    def test_export_faults_format_parameter(self, client: TestClient, auth_headers: dict[str, str]):
        """Test faults export with format parameter"""
        response = client.post(
            "/export/faults",
            params={"format": "csv"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Faults already export as CSV by default
        assert data["key"].endswith(".csv")
