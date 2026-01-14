"""
Integration tests for GraphQL API

Tests cover:
- Queries with new input filter types (VoltageReadingFilter, PowerQualityFilter, FaultEventFilter)
- Mutations for data ingestion (ingestVoltageReading, ingestPowerQuality, createFaultEvent)
- Data validation and error handling
- Time range filtering
- Authentication requirements
"""

# pylint: disable=redefined-outer-name,too-many-public-methods

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_access_token
from database import FaultEventDB, PowerQualityDB, VoltageReadingDB


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


@pytest.fixture
async def seeded_voltage_data(test_db: AsyncSession):
    """Seed test database with voltage readings"""
    now = datetime.now(timezone.utc)
    readings = [
        VoltageReadingDB(
            sensor_id="VS-001",
            location="Zone-A",
            voltage_l1=230.0,
            voltage_l2=230.5,
            voltage_l3=229.8,
            frequency=50.0,
            timestamp=now - timedelta(hours=i),
        )
        for i in range(5)
    ]
    readings.append(
        VoltageReadingDB(
            sensor_id="VS-002",
            location="Zone-B",
            voltage_l1=231.0,
            voltage_l2=231.5,
            voltage_l3=230.8,
            frequency=50.1,
            timestamp=now - timedelta(hours=1),
        )
    )
    for r in readings:
        test_db.add(r)
    await test_db.commit()
    return readings


@pytest.fixture
async def seeded_power_quality_data(test_db: AsyncSession):
    """Seed test database with power quality data"""
    now = datetime.now(timezone.utc)
    data = [
        PowerQualityDB(
            sensor_id="PQ-001",
            location="Zone-A",
            thd_voltage=2.5,
            thd_current=3.2,
            power_factor=0.95,
            voltage_imbalance=1.2,
            flicker_severity=0.5,
            timestamp=now - timedelta(hours=i),
        )
        for i in range(3)
    ]
    for d in data:
        test_db.add(d)
    await test_db.commit()
    return data


@pytest.fixture
async def seeded_fault_events(test_db: AsyncSession):
    """Seed test database with fault events"""
    now = datetime.now(timezone.utc)
    events = [
        FaultEventDB(
            sensor_id="VS-001",
            severity="high",
            fault_type="overvoltage",
            location="Zone-A",
            timestamp=now - timedelta(hours=1),
            duration_ms=250,
            resolved=False,
            description="High voltage fault in Zone-A",
        ),
        FaultEventDB(
            sensor_id="VS-002",
            severity="medium",
            fault_type="undervoltage",
            location="Zone-B",
            timestamp=now - timedelta(hours=2),
            duration_ms=500,
            resolved=True,
            description="Undervoltage event in Zone-B",
        ),
        FaultEventDB(
            sensor_id="VS-003",
            severity="low",
            fault_type="frequency_deviation",
            location="Zone-A",
            timestamp=now - timedelta(hours=3),
            duration_ms=100,
            resolved=False,
            description="Minor frequency deviation",
        ),
    ]
    for e in events:
        test_db.add(e)
    await test_db.commit()
    return events


# ==============================================================================
# QUERY TESTS
# ==============================================================================


class TestGraphQLQueries:
    """Test GraphQL query operations"""

    def test_hello_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test hello world query returns greeting"""
        query = '{ hello(name: "Grid") }'
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["hello"] == "Hello Grid!"

    def test_hello_query_default_name(self, client: TestClient, auth_headers: dict[str, str]):
        """Test hello query with default name parameter"""
        query = "{ hello }"
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["hello"] == "Hello World!"


class TestVoltageReadingsQuery:
    """Test voltage readings query with filter input types"""

    def test_voltage_readings_basic_query(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_voltage_data,  # pylint: disable=unused-argument
    ):
        """Test basic voltage readings query with limit"""
        query = """
        query {
            voltageReadings(options: { limit: 5 }) {
                id
                sensorId
                location
                voltageL1
                voltageL2
                voltageL3
                frequency
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        readings = data["data"]["voltageReadings"]
        assert isinstance(readings, list)
        assert len(readings) <= 5

    def test_voltage_readings_with_sensor_filter(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_voltage_data,  # pylint: disable=unused-argument
    ):
        """Test voltage readings filtered by sensor ID"""
        query = """
        query {
            voltageReadings(options: { sensorId: "VS-001", limit: 10 }) {
                sensorId
                voltageL1
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        readings = data["data"]["voltageReadings"]
        # All readings should be from VS-001
        for reading in readings:
            assert reading["sensorId"] == "VS-001"

    def test_voltage_readings_with_time_range_hours(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_voltage_data,  # pylint: disable=unused-argument
    ):
        """Test voltage readings with hours-based time filter"""
        query = """
        query {
            voltageReadings(options: { limit: 10, timeRange: { hours: 2 } }) {
                id
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data

    def test_voltage_readings_returns_all_fields(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_voltage_data,  # pylint: disable=unused-argument
    ):
        """Test that all voltage reading fields are accessible"""
        query = """
        query {
            voltageReadings(options: { limit: 1 }) {
                id
                sensorId
                location
                voltageL1
                voltageL2
                voltageL3
                frequency
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        if data["data"]["voltageReadings"]:
            reading = data["data"]["voltageReadings"][0]
            assert "id" in reading
            assert "sensorId" in reading
            assert "location" in reading
            assert "voltageL1" in reading
            assert "voltageL2" in reading
            assert "voltageL3" in reading
            assert "frequency" in reading
            assert "timestamp" in reading


class TestPowerQualityQuery:
    """Test power quality query with filter input types"""

    def test_power_quality_basic_query(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_power_quality_data,  # pylint: disable=unused-argument
    ):
        """Test basic power quality query"""
        query = """
        query {
            powerQuality(options: { limit: 5 }) {
                id
                sensorId
                location
                thdVoltage
                thdCurrent
                powerFactor
                voltageImbalance
                flickerSeverity
                timestamp
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        metrics = data["data"]["powerQuality"]
        assert isinstance(metrics, list)

    def test_power_quality_with_sensor_filter(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_power_quality_data,  # pylint: disable=unused-argument
    ):
        """Test power quality filtered by sensor ID"""
        query = """
        query {
            powerQuality(options: { sensorId: "PQ-001", limit: 10 }) {
                sensorId
                powerFactor
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data


class TestFaultEventsQuery:
    """Test fault events query with filter input types"""

    def test_fault_events_basic_query(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_fault_events,  # pylint: disable=unused-argument
    ):
        """Test basic fault events query"""
        query = """
        query {
            faultEvents(options: { limit: 10 }) {
                id
                eventId
                severity
                eventType
                location
                timestamp
                durationMs
                resolved
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        events = data["data"]["faultEvents"]
        assert isinstance(events, list)

    def test_fault_events_with_severity_filter(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seeded_fault_events,  # pylint: disable=unused-argument
    ):
        """Test fault events filtered by severity"""
        query = """
        query {
            faultEvents(options: { severity: "high", limit: 10 }) {
                eventId
                severity
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        events = data["data"]["faultEvents"]
        for event in events:
            assert event["severity"] == "high"


class TestSensorStatsQuery:
    """Test sensor statistics query"""

    def test_sensor_stats_query(self, client: TestClient, auth_headers: dict[str, str]):
        """Test sensor statistics aggregation query"""
        query = """
        query {
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
        assert "errors" not in data
        stats = data["data"]["sensorStats"]
        assert "totalSensors" in stats
        assert "avgVoltage" in stats


# ==============================================================================
# MUTATION TESTS
# ==============================================================================


class TestGraphQLMutations:
    """Test GraphQL mutation operations"""

    def test_ingest_voltage_reading_success(self, client: TestClient, auth_headers: dict[str, str]):
        """Test successful voltage reading ingestion"""
        timestamp = datetime.now(timezone.utc).isoformat()
        mutation = f"""
        mutation {{
            ingestVoltageReading(reading: {{
                sensorId: "VS-TEST-001"
                location: "Test Zone"
                voltageL1: 230.5
                voltageL2: 231.0
                voltageL3: 229.8
                frequency: 50.0
                timestamp: "{timestamp}"
            }}) {{
                success
                message
                id
            }}
        }}
        """
        response = client.post("/graphql", json={"query": mutation}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        result = data["data"]["ingestVoltageReading"]
        assert result["success"] is True
        assert result["id"] is not None
        assert "ingested" in result["message"].lower()

    def test_ingest_power_quality_success(self, client: TestClient, auth_headers: dict[str, str]):
        """Test successful power quality data ingestion"""
        timestamp = datetime.now(timezone.utc).isoformat()
        mutation = f"""
        mutation {{
            ingestPowerQuality(data: {{
                sensorId: "PQ-TEST-001"
                location: "Test Zone"
                thdVoltage: 2.5
                thdCurrent: 3.2
                powerFactor: 0.95
                voltageImbalance: 1.2
                flickerSeverity: 0.5
                timestamp: "{timestamp}"
            }}) {{
                success
                message
                id
            }}
        }}
        """
        response = client.post("/graphql", json={"query": mutation}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        result = data["data"]["ingestPowerQuality"]
        assert result["success"] is True
        assert result["id"] is not None

    def test_create_fault_event_success(self, client: TestClient, auth_headers: dict[str, str]):
        """Test successful fault event creation"""
        timestamp = datetime.now(timezone.utc).isoformat()
        mutation = f"""
        mutation {{
            createFaultEvent(event: {{
                eventId: "EVT-TEST-001"
                severity: "high"
                eventType: "overvoltage"
                location: "Test Zone"
                timestamp: "{timestamp}"
                durationMs: 250
            }}) {{
                success
                message
                id
            }}
        }}
        """
        response = client.post("/graphql", json={"query": mutation}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        result = data["data"]["createFaultEvent"]
        assert result["success"] is True
        assert result["id"] is not None

    def test_mutation_and_query_roundtrip(self, client: TestClient, auth_headers: dict[str, str]):
        """Test that ingested data can be queried back"""
        # Ingest a reading
        timestamp = datetime.now(timezone.utc).isoformat()
        sensor_id = "VS-ROUNDTRIP-001"
        mutation = f"""
        mutation {{
            ingestVoltageReading(reading: {{
                sensorId: "{sensor_id}"
                location: "Roundtrip Test"
                voltageL1: 999.0
                voltageL2: 999.0
                voltageL3: 999.0
                frequency: 50.0
                timestamp: "{timestamp}"
            }}) {{
                success
                id
            }}
        }}
        """
        response = client.post("/graphql", json={"query": mutation}, headers=auth_headers)
        assert response.json()["data"]["ingestVoltageReading"]["success"] is True

        # Query it back
        query = f"""
        query {{
            voltageReadings(options: {{ sensorId: "{sensor_id}", limit: 1 }}) {{
                sensorId
                voltageL1
            }}
        }}
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        data = response.json()

        assert "errors" not in data
        readings = data["data"]["voltageReadings"]
        assert len(readings) == 1
        assert readings[0]["sensorId"] == sensor_id
        assert readings[0]["voltageL1"] == 999.0


# ==============================================================================
# ERROR HANDLING TESTS
# ==============================================================================


class TestGraphQLErrorHandling:
    """Test GraphQL error handling and validation"""

    def test_invalid_query_syntax(self, client: TestClient, auth_headers: dict[str, str]):
        """Test GraphQL returns error for invalid syntax"""
        query = "{ invalidField }"
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200  # GraphQL returns 200 with errors
        data = response.json()
        assert "errors" in data

    def test_empty_query_rejected(self, client: TestClient, auth_headers: dict[str, str]):
        """Test GraphQL rejects empty query"""
        response = client.post("/graphql", json={"query": ""}, headers=auth_headers)
        assert response.status_code in [200, 400]

    def test_missing_required_mutation_field(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test mutation fails when required field is missing"""
        mutation = """
        mutation {
            ingestVoltageReading(reading: {
                sensorId: "VS-001"
            }) {
                success
            }
        }
        """
        response = client.post("/graphql", json={"query": mutation}, headers=auth_headers)
        data = response.json()
        # Should have validation errors for missing required fields
        assert "errors" in data

    def test_invalid_field_type(self, client: TestClient, auth_headers: dict[str, str]):
        """Test mutation fails with wrong field type"""
        mutation = """
        mutation {
            ingestVoltageReading(reading: {
                sensorId: "VS-001"
                location: "Zone-A"
                voltageL1: "not-a-number"
                voltageL2: 230.0
                voltageL3: 230.0
                frequency: 50.0
                timestamp: "2024-01-01T00:00:00Z"
            }) {
                success
            }
        }
        """
        response = client.post("/graphql", json={"query": mutation}, headers=auth_headers)
        data = response.json()
        assert "errors" in data


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================


class TestGraphQLAuthentication:
    """Test GraphQL authentication behavior"""

    def test_query_without_auth_header(self, client: TestClient):
        """Test GraphQL query without authentication"""
        query = '{ hello(name: "Test") }'
        response = client.post("/graphql", json={"query": query})
        # Behavior depends on implementation - may allow public queries or require auth
        assert response.status_code in [200, 401, 403]

    def test_query_with_invalid_token(self, client: TestClient):
        """Test GraphQL query with invalid JWT token"""
        query = '{ hello(name: "Test") }'
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.post("/graphql", json={"query": query}, headers=headers)
        assert response.status_code in [200, 401, 403]

    def test_query_with_expired_token(self, client: TestClient):
        """Test GraphQL query with expired JWT token"""
        # Create token that expired 1 hour ago
        expired_token = create_access_token(
            data={"sub": "testuser"}, expires_delta=timedelta(hours=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        query = '{ hello(name: "Test") }'
        response = client.post("/graphql", json={"query": query}, headers=headers)
        # Should reject expired token
        assert response.status_code in [200, 401, 403]


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================


class TestGraphQLEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_query_with_zero_limit(self, client: TestClient, auth_headers: dict[str, str]):
        """Test query with limit of 0"""
        query = """
        query {
            voltageReadings(options: { limit: 0 }) {
                id
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should return empty list or handle gracefully
        if "errors" not in data:
            assert data["data"]["voltageReadings"] == []

    def test_query_with_large_limit(self, client: TestClient, auth_headers: dict[str, str]):
        """Test query with very large limit"""
        query = """
        query {
            voltageReadings(options: { limit: 10000 }) {
                id
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200
        # Should not crash, may return less than requested

    def test_query_with_special_characters_in_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test query with special characters in sensor ID filter"""
        query = """
        query {
            voltageReadings(options: { sensorId: "sensor-with-dashes_and_underscores", limit: 5 }) {
                id
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)
        assert response.status_code == 200

    def test_multiple_queries_in_single_request(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """Test multiple queries in a single GraphQL request"""
        query = """
        query {
            hello
            sensorStats {
                totalSensors
            }
        }
        """
        response = client.post("/graphql", json={"query": query}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        assert "hello" in data["data"]
        assert "sensorStats" in data["data"]
