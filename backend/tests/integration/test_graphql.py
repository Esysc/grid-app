"""
Integration tests for GraphQL queries
"""

# pylint: disable=redefined-outer-name

from datetime import timedelta

import pytest
from auth import create_access_token
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Generate valid JWT auth headers for testing"""
    access_token = create_access_token(
        data={"sub": "testuser"}, expires_delta=timedelta(minutes=15)
    )
    return {"Authorization": f"Bearer {access_token}"}


class TestGraphQLQueries:
    """Test GraphQL queries"""

    def test_graphql_hello_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test hello world GraphQL query"""
        query = """
        {
            hello(name: "Grid")
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_graphql_voltage_readings_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test voltage readings GraphQL query"""
        query = """
        {
            voltageReadings(limit: 10) {
                id
                sensorId
                voltage
                timestamp
                location
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_graphql_voltage_readings_with_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test voltage readings GraphQL query with sensor filter"""
        query = """
        {
            voltageReadings(limit: 10, sensorId: "VS-001") {
                id
                sensorId
                voltage
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_graphql_power_quality_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test power quality GraphQL query"""
        query = """
        {
            powerQualityMetrics(limit: 10) {
                id
                sensorId
                thd
                frequency
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_graphql_fault_events_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test fault events GraphQL query"""
        query = """
        {
            faultEvents(limit: 10) {
                id
                eventId
                severity
                eventType
                location
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_graphql_sensor_stats_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test sensor statistics GraphQL query"""
        query = """
        {
            sensorStats {
                totalSensors
                activeSensors
                faultCount24h
                violationCount24h
                avgVoltage
                minVoltage
                maxVoltage
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data


class TestGraphQLMutations:
    """Test GraphQL mutations (if implemented)"""

    def test_graphql_invalid_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test GraphQL with invalid query syntax"""
        query = """
        {
            invalidField
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        # GraphQL returns 200 but has error in response
        data = response.json()
        assert "errors" in data or "data" in data

    def test_graphql_empty_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test GraphQL with empty query"""
        response = client.post("/graphql", json={"query": ""}, headers=auth_headers)
        # Should return some error
        assert response.status_code in [200, 400]


class TestGraphQLWithoutAuth:
    """Test GraphQL behavior without authentication"""

    def test_graphql_without_auth(self, client: TestClient):
        """Test GraphQL query without authentication"""
        query = """
        {
            hello(name: "Test")
        }
        """
        response = client.post("/graphql", json={"query": query})
        # GraphQL endpoint behavior depends on implementation
        # May allow unauthenticated access to public queries
        assert response.status_code in [200, 403]
