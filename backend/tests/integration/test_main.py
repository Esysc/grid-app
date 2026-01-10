"""
Tests for Grid Monitoring API
"""

import math
from datetime import datetime, timezone

import pytest
from auth import (
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_password_hash,
    verify_password,
)
from data_generator import GridDataGenerator
from database import Base
from models import FaultEvent, PowerQualityMetrics, VoltageReading
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool


# Test database setup
@pytest.fixture
async def test_db():
    """Create a test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestDataGenerator:
    """Tests for the data generator"""

    def test_generate_voltage_reading(self):
        """Test voltage reading generation"""
        generator = GridDataGenerator()
        reading = generator.generate_voltage_reading()

        assert any(reading.sensor_id.startswith(p) for p in ["sensor-", "VS-", "PQ-", "FS-"])
        assert 210 < reading.voltage_l1 < 250
        assert 210 < reading.voltage_l2 < 250
        assert 210 < reading.voltage_l3 < 250
        assert reading.location in GridDataGenerator.LOCATIONS

    def test_generate_power_quality(self):
        """Test power quality generation"""
        generator = GridDataGenerator()
        pq = generator.generate_power_quality()

        assert any(pq.sensor_id.startswith(p) for p in ["sensor-", "VS-", "PQ-", "FS-"])
        assert 0 < pq.thd_voltage < 15
        assert 0.7 < pq.power_factor <= 1.0
        assert 0 < pq.thd_current < 15

    def test_generate_fault_event(self):
        """Test fault event generation"""
        generator = GridDataGenerator()
        fault = generator.generate_fault_event()

        assert any(fault.sensor_id.startswith(p) for p in ["sensor-", "VS-", "PQ-", "FS-"])
        assert fault.severity in ["low", "medium", "high", "critical", "minor", "major"]
        assert fault.fault_type in [
            "overvoltage",
            "undervoltage",
            "harmonics",
            "imbalance",
            "short_circuit",
            "ground_fault",
        ]
        assert fault.duration_ms is None or fault.duration_ms > 0

    def test_generate_historical_data(self):
        """Test historical data generation"""
        generator = GridDataGenerator()
        voltage, pq, faults = generator.generate_historical_data(hours=1)

        assert len(voltage) > 0
        assert len(pq) > 0
        assert len(faults) > 0
        assert all(isinstance(v, VoltageReading) for v in voltage)
        assert all(isinstance(p, PowerQualityMetrics) for p in pq)
        assert all(isinstance(f, FaultEvent) for f in faults)


class TestModels:
    """Tests for Pydantic models"""

    def test_voltage_reading_model(self):
        """Test VoltageReading model validation"""
        reading = VoltageReading(
            sensor_id="sensor-1",
            voltage_l1=230.0,
            voltage_l2=231.0,
            voltage_l3=229.0,
            frequency=50.0,
            location="Zone-1",
            timestamp=datetime.now(timezone.utc),
        )
        assert math.isclose(reading.voltage_l1, 230.0)

    def test_power_quality_model(self):
        """Test PowerQualityMetrics model validation"""
        pq = PowerQualityMetrics(
            sensor_id="sensor-1",
            thd_voltage=2.5,
            thd_current=3.0,
            power_factor=0.95,
            voltage_imbalance=1.5,
            flicker_severity=0.5,
            location="Zone-1",
            timestamp=datetime.now(timezone.utc),
        )
        assert math.isclose(pq.thd_voltage, 2.5)

    def test_fault_event_model(self):
        """Test FaultEvent model validation"""
        fault = FaultEvent(
            sensor_id="sensor-1",
            fault_type="overvoltage",
            severity="high",
            voltage_drop=15.0,
            duration_ms=500,
            location="Zone-1",
            timestamp=datetime.now(timezone.utc),
            description="Test fault event",
        )
        assert fault.sensor_id == "sensor-1"
        assert fault.severity == "high"
        assert fault.fault_type == "overvoltage"


class TestAuthentication:
    """Tests for authentication"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_password(self):
        """Test password verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_authenticate_user(self):
        """Test user authentication"""
        # Default test user: username=admin, password=secret
        user = authenticate_user(fake_users_db, "admin", "secret")
        assert user is not None
        assert user.username == "admin"

        user = authenticate_user(fake_users_db, "admin", "wrong_password")
        assert user is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
