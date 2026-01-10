"""
Integration tests for FastAPI endpoints
"""

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta, timezone
from typing import TypedDict

import pytest
from auth import create_access_token
from fastapi.testclient import TestClient
from main import app


class VoltagePayload(TypedDict):
    """Type definition for voltage reading payload"""

    sensor_id: str
    location: str
    timestamp: str
    voltage_l1: float
    voltage_l2: float
    voltage_l3: float
    frequency: float


class PowerQualityPayload(TypedDict):
    """Type definition for power quality payload"""

    sensor_id: str
    location: str
    timestamp: str
    thd_voltage: float
    thd_current: float
    power_factor: float
    voltage_imbalance: float
    flicker_severity: float


class FaultEventPayload(TypedDict):
    """Type definition for fault event payload"""

    timestamp: str
    sensor_id: str
    location: str
    fault_type: str
    severity: str
    voltage_drop: float
    duration_ms: int
    resolved: bool
    description: str


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Generate valid JWT auth headers for testing"""
    access_token = create_access_token(data={"sub": "admin"}, expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {access_token}"}


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Grid Monitoring API"
        assert data["version"] == "2.0.0"
        assert "docs" in data
        assert "graphql" in data


class TestHealthCheckEndpoint:
    """Test health check endpoint"""

    def test_health_check_success(self, client: TestClient):
        """Test health check endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "database_connected" in data


class TestAuthenticationEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self, client: TestClient):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            data={
                "username": "admin",
                "password": "secret",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login",
            data={
                "username": "admin",
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "password",
            },
        )
        assert response.status_code == 401

    def test_get_current_user_profile(self, client: TestClient, auth_headers: dict[str, str]):
        """Test getting current user profile"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data

    def test_get_current_user_profile_unauthorized(self, client: TestClient):
        """Test getting current user profile without auth"""
        response = client.get("/auth/me")
        assert response.status_code == 403  # Forbidden, no auth header

    def test_get_current_user_profile_invalid_token(self, client: TestClient):
        """Test getting current user profile with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401


class TestVoltageReadingsEndpoint:
    """Test voltage readings endpoint"""

    def test_voltage_readings_unauthorized(self, client: TestClient):
        """Test voltage readings without auth"""
        response = client.get("/sensors/voltage")
        assert response.status_code == 403

    def test_voltage_readings_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test voltage readings with authentication"""
        response = client.get("/sensors/voltage", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_voltage_readings_with_hours_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test voltage readings with hours filter"""
        response = client.get("/sensors/voltage?hours=24", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_voltage_readings_with_sensor_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test voltage readings with sensor ID filter"""
        response = client.get("/sensors/voltage?sensor_id=VS-001", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_voltage_readings_invalid_hours(self, client: TestClient, auth_headers: dict[str, str]):
        """Test voltage readings with invalid hours parameter"""
        response = client.get("/sensors/voltage?hours=200", headers=auth_headers)
        # Should reject hours > 168
        assert response.status_code == 422

    def test_voltage_readings_zero_hours(self, client: TestClient, auth_headers: dict[str, str]):
        """Test voltage readings with zero hours parameter"""
        response = client.get("/sensors/voltage?hours=0", headers=auth_headers)
        # Should reject hours < 1
        assert response.status_code == 422


class TestPowerQualityEndpoint:
    """Test power quality endpoint"""

    def test_power_quality_unauthorized(self, client: TestClient):
        """Test power quality without auth"""
        response = client.get("/sensors/power-quality")
        assert response.status_code == 403

    def test_power_quality_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test power quality with authentication"""
        response = client.get("/sensors/power-quality", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_power_quality_with_hours_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test power quality with hours filter"""
        response = client.get("/sensors/power-quality?hours=12", headers=auth_headers)
        assert response.status_code == 200

    def test_power_quality_with_sensor_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test power quality with sensor ID filter"""
        response = client.get("/sensors/power-quality?sensor_id=PQ-001", headers=auth_headers)
        assert response.status_code == 200


class TestFaultsEndpoints:
    """Test fault events endpoints"""

    def test_recent_faults_unauthorized(self, client: TestClient):
        """Test recent faults without auth"""
        response = client.get("/faults/recent")
        assert response.status_code == 403

    def test_recent_faults_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test recent faults with authentication"""
        response = client.get("/faults/recent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_recent_faults_with_hours_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test recent faults with hours filter"""
        response = client.get("/faults/recent?hours=48", headers=auth_headers)
        assert response.status_code == 200

    def test_recent_faults_with_severity_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test recent faults with severity filter"""
        response = client.get("/faults/recent?severity=critical", headers=auth_headers)
        assert response.status_code == 200

    def test_fault_timeline_unauthorized(self, client: TestClient):
        """Test fault timeline without auth"""
        response = client.get("/faults/timeline")
        assert response.status_code == 403

    def test_fault_timeline_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test fault timeline with authentication"""
        response = client.get("/faults/timeline", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_fault_timeline_with_date_range(self, client: TestClient, auth_headers: dict[str, str]):
        """Test fault timeline with date range"""
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()

        response = client.get(
            "/faults/timeline",
            params={"start_date": start_date, "end_date": end_date},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestSensorStatsEndpoint:
    """Test sensor statistics endpoint"""

    def test_sensor_stats_unauthorized(self, client: TestClient):
        """Test sensor stats without auth"""
        response = client.get("/stats")
        assert response.status_code == 403

    def test_sensor_stats_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test sensor stats with authentication"""
        response = client.get("/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_sensors" in data
        assert "active_sensors" in data
        assert "total_faults_24h" in data


class TestIngestEndpoints:
    """Test data ingestion endpoints"""

    def test_ingest_voltage_unauthorized(self, client: TestClient):
        """Test voltage ingestion without auth"""
        payload: VoltagePayload = {
            "sensor_id": "VS-001",
            "location": "Substation A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "voltage_l1": 230.0,
            "voltage_l2": 230.0,
            "voltage_l3": 230.0,
            "frequency": 50.0,
        }
        response = client.post("/sensors/voltage", json=payload)
        assert response.status_code == 403

    def test_ingest_voltage_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test voltage ingestion with authentication"""
        payload: VoltagePayload = {
            "sensor_id": "VS-001",
            "location": "Substation A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "voltage_l1": 230.0,
            "voltage_l2": 230.0,
            "voltage_l3": 230.0,
            "frequency": 50.0,
        }
        response = client.post("/sensors/voltage", json=payload, headers=auth_headers)
        assert response.status_code == 201

    def test_ingest_voltage_invalid_data(self, client: TestClient, auth_headers: dict[str, str]):
        """Test voltage ingestion with invalid data"""
        payload: VoltagePayload = {
            "sensor_id": "VS-001",
            "location": "Substation A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "voltage_l1": 600000,  # Exceeds max
            "voltage_l2": 230.0,
            "voltage_l3": 230.0,
            "frequency": 50.0,
        }
        response = client.post("/sensors/voltage", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_ingest_power_quality_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test power quality ingestion with authentication"""
        payload: PowerQualityPayload = {
            "sensor_id": "PQ-001",
            "location": "Substation A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "thd_voltage": 2.5,
            "thd_current": 3.2,
            "power_factor": 0.95,
            "voltage_imbalance": 1.2,
            "flicker_severity": 0.8,
        }
        response = client.post("/sensors/power-quality", json=payload, headers=auth_headers)
        assert response.status_code == 201

    def test_ingest_fault_event_with_auth(self, client: TestClient, auth_headers: dict[str, str]):
        """Test fault event ingestion with authentication"""
        payload: FaultEventPayload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sensor_id": "FS-001",
            "location": "Feeder 3B",
            "fault_type": "short_circuit",
            "severity": "critical",
            "voltage_drop": 85.5,
            "duration_ms": 150,
            "resolved": True,
            "description": "Phase-to-ground short circuit detected",
        }
        response = client.post("/faults", json=payload, headers=auth_headers)
        assert response.status_code == 201
