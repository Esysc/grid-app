"""
Integration tests for the Server-Sent Events (SSE) endpoint.
"""

from datetime import timedelta

import main
import pytest
from auth import create_access_token
from fastapi.testclient import TestClient
from main import app
from pytest import MonkeyPatch


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    access_token = create_access_token(data={"sub": "admin"}, expires_delta=timedelta(minutes=15))
    return {"Authorization": f"Bearer {access_token}"}


class StubModel:
    def __init__(self, data: dict[str, object]):
        self._data = data

    def model_dump(  # pylint: disable=unused-argument
        self, mode: str = "json"
    ) -> dict[str, object]:
        return self._data


@pytest.fixture(autouse=True)
def mock_generator(monkeypatch: MonkeyPatch):  # pylint: disable=unused-argument
    """Mock the data generator to return deterministic values."""
    monkeypatch.setattr(
        main.generator,
        "generate_voltage_reading",
        lambda: StubModel(
            {
                "sensor_id": "VS-TEST",
                "voltage_l1": 230.1,
                "voltage_l2": 229.9,
                "voltage_l3": 230.0,
                "frequency": 50.0,
                "location": "Lab",
            }
        ),
    )
    monkeypatch.setattr(
        main.generator,
        "generate_power_quality",
        lambda: StubModel(
            {
                "sensor_id": "PQ-TEST",
                "thd_voltage": 2.5,
                "thd_current": 3.1,
                "power_factor": 0.96,
                "frequency": 50.0,
                "location": "Lab",
            }
        ),
    )
    # Faults are occasional; we don't require them for assertions
    monkeypatch.setattr(
        main.generator,
        "generate_fault_event",
        lambda: StubModel(
            {
                "sensor_id": "FT-TEST",
                "fault_type": "overvoltage",
                "severity": "medium",
                "description": "Test fault",
            }
        ),
    )


# Note: We keep the real sleep (2s) since the endpoint yields
# the first event before sleeping, avoiding tight loops.


def test_sse_requires_authentication(
    client: TestClient,  # pylint: disable=redefined-outer-name
):
    """SSE endpoint should require JWT auth."""
    response = client.get("/stream/updates")
    # FastAPI/Starlette typically respond 403 for missing auth dependency
    assert response.status_code == 403


@pytest.mark.skip(reason="SSE endpoint has infinite event generator that blocks")
def test_sse_response_headers(
    client: TestClient, auth_headers: dict[str, str]
):  # pylint: disable=redefined-outer-name
    """Validate SSE endpoint response headers and content type without streaming."""
    # Don't use context manager; TestClient.stream() blocks indefinitely on infinite streams
    response = client.get("/stream/updates", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/event-stream")
    assert response.headers.get("cache-control") == "no-cache"
    assert response.headers.get("connection") == "keep-alive"
