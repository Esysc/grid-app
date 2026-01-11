"""
Shared pytest fixtures and configuration
"""

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator, Dict

import pytest
from auth import create_access_token
from database import Base, get_db
from main import app
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Generate valid JWT auth headers for testing"""
    access_token = create_access_token(data={"sub": "admin"}, expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_db() -> AsyncIterator[AsyncSession]:
    """Create an in-memory SQLite database for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture(autouse=True)
async def override_get_db(test_db: AsyncSession):
    """Override get_db dependency globaly for all tests"""
    app.dependency_overrides[get_db] = lambda: test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_voltage_reading() -> Dict[str, Any]:
    """Sample voltage reading data for testing"""
    return {
        "sensor_id": "sensor-001",
        "voltage_l1": 230.0,
        "voltage_l2": 230.5,
        "voltage_l3": 229.8,
        "location": "Zone-A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_power_quality() -> Dict[str, Any]:
    """Sample power quality data for testing"""
    return {
        "sensor_id": "sensor-001",
        "thd_voltage": 2.5,
        "thd_current": 3.2,
        "power_factor": 0.95,
        "frequency": 50.0,
        "location": "Zone-A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_fault_event() -> Dict[str, Any]:
    """Sample fault event data for testing"""
    return {
        "sensor_id": "sensor-001",
        "fault_type": "overvoltage",
        "severity": "medium",
        "location": "Zone-A",
        "voltage_drop": 15.5,
        "duration_ms": 250,
        "description": "Voltage spike detected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
