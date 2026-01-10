"""
Unit tests for Pydantic models validation
"""

import math
from datetime import datetime, timezone
from typing import Any

import pytest
from models import FaultEvent, PowerQualityMetrics, VoltageReading


class TestVoltageReading:
    """Test VoltageReading model validation"""

    def test_valid_voltage_reading(self):
        """Test creating a valid voltage reading"""
        reading = VoltageReading(
            sensor_id="VS-001",
            location="Substation A",
            timestamp=datetime.now(timezone.utc),
            voltage_l1=230.5,
            voltage_l2=231.2,
            voltage_l3=229.8,
            frequency=50.0,
        )
        assert reading.sensor_id == "VS-001"
        assert reading.location == "Substation A"
        assert math.isclose(reading.voltage_l1, 230.5)
        assert math.isclose(reading.frequency, 50.0)

    def test_voltage_reading_invalid_voltage_too_high(self):
        """Test voltage reading with voltage exceeding max"""
        with pytest.raises(ValueError):
            VoltageReading(
                sensor_id="VS-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                voltage_l1=500001,  # Exceeds max of 500000
                voltage_l2=231.2,
                voltage_l3=229.8,
                frequency=50.0,
            )

    def test_voltage_reading_invalid_voltage_negative(self):
        """Test voltage reading with negative voltage"""
        with pytest.raises(ValueError):
            VoltageReading(
                sensor_id="VS-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                voltage_l1=-100,  # Negative voltage
                voltage_l2=231.2,
                voltage_l3=229.8,
                frequency=50.0,
            )

    def test_voltage_reading_invalid_frequency_too_high(self):
        """Test voltage reading with frequency exceeding max"""
        with pytest.raises(ValueError):
            VoltageReading(
                sensor_id="VS-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                voltage_l1=230.5,
                voltage_l2=231.2,
                voltage_l3=229.8,
                frequency=66.0,  # Exceeds max of 65
            )

    def test_voltage_reading_invalid_frequency_too_low(self):
        """Test voltage reading with frequency below min"""
        with pytest.raises(ValueError):
            VoltageReading(
                sensor_id="VS-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                voltage_l1=230.5,
                voltage_l2=231.2,
                voltage_l3=229.8,
                frequency=44.0,  # Below min of 45
            )

    def test_voltage_reading_missing_required_field(self):
        """Test voltage reading with missing required field"""
        data: dict[str, Any] = {
            "sensor_id": "VS-001",
            "location": "Substation A",
            "timestamp": datetime.now(timezone.utc),
            "voltage_l1": 230.5,
            "voltage_l2": 231.2,
            # Missing voltage_l3
            "frequency": 50.0,
        }
        with pytest.raises(ValueError):
            VoltageReading(**data)

    def test_voltage_reading_boundary_values(self):
        """Test voltage reading with boundary values"""
        reading = VoltageReading(
            sensor_id="VS-001",
            location="Substation A",
            timestamp=datetime.now(timezone.utc),
            voltage_l1=0,  # Min
            voltage_l2=500000,  # Max
            voltage_l3=230.0,  # Normal
            frequency=45.0,  # Min frequency
        )
        assert math.isclose(reading.voltage_l1, 0, abs_tol=1e-9)
        assert math.isclose(reading.voltage_l2, 500000)
        assert math.isclose(reading.frequency, 45.0)


class TestPowerQualityMetrics:
    """Test PowerQualityMetrics model validation"""

    def test_valid_power_quality(self):
        """Test creating valid power quality metrics"""
        pq = PowerQualityMetrics(
            sensor_id="PQ-001",
            location="Substation A",
            timestamp=datetime.now(timezone.utc),
            thd_voltage=2.5,
            thd_current=3.2,
            power_factor=0.95,
            voltage_imbalance=1.2,
            flicker_severity=0.8,
        )
        assert pq.sensor_id == "PQ-001"
        assert math.isclose(pq.thd_voltage, 2.5)
        assert math.isclose(pq.power_factor, 0.95)

    def test_power_quality_invalid_thd_voltage_too_high(self):
        """Test THD voltage exceeding max"""
        with pytest.raises(ValueError):
            PowerQualityMetrics(
                sensor_id="PQ-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                thd_voltage=101.0,  # Exceeds max of 100
                thd_current=3.2,
                power_factor=0.95,
                voltage_imbalance=1.2,
                flicker_severity=0.8,
            )

    def test_power_quality_invalid_power_factor_too_high(self):
        """Test power factor exceeding max"""
        with pytest.raises(ValueError):
            PowerQualityMetrics(
                sensor_id="PQ-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                thd_voltage=2.5,
                thd_current=3.2,
                power_factor=1.5,  # Exceeds max of 1.0
                voltage_imbalance=1.2,
                flicker_severity=0.8,
            )

    def test_power_quality_invalid_power_factor_too_low(self):
        """Test power factor below min"""
        with pytest.raises(ValueError):
            PowerQualityMetrics(
                sensor_id="PQ-001",
                location="Substation A",
                timestamp=datetime.now(timezone.utc),
                thd_voltage=2.5,
                thd_current=3.2,
                power_factor=-1.5,  # Below min of -1.0
                voltage_imbalance=1.2,
                flicker_severity=0.8,
            )

    def test_power_quality_boundary_values(self):
        """Test power quality with boundary values"""
        pq = PowerQualityMetrics(
            sensor_id="PQ-001",
            location="Substation A",
            timestamp=datetime.now(timezone.utc),
            thd_voltage=0,  # Min
            thd_current=100,  # Max
            power_factor=-1.0,  # Min
            voltage_imbalance=0,  # Min
            flicker_severity=10,  # Max
        )
        assert math.isclose(pq.thd_voltage, 0, abs_tol=1e-9)
        assert math.isclose(pq.thd_current, 100)
        assert math.isclose(pq.power_factor, -1.0)
        assert math.isclose(pq.flicker_severity, 10)


class TestFaultEvent:
    """Test FaultEvent model validation"""

    def test_valid_fault_event(self):
        """Test creating a valid fault event"""
        fault = FaultEvent(
            timestamp=datetime.now(timezone.utc),
            sensor_id="FS-001",
            location="Feeder 3B",
            fault_type="short_circuit",
            severity="critical",
            voltage_drop=85.5,
            duration_ms=150,
            resolved=True,
            description="Phase-to-ground short circuit detected",
        )
        assert fault.sensor_id == "FS-001"
        assert fault.fault_type == "short_circuit"
        assert fault.severity == "critical"
        assert fault.resolved is True

    def test_fault_event_without_optional_fields(self):
        """Test fault event with only required fields"""
        fault = FaultEvent(
            timestamp=datetime.now(timezone.utc),
            sensor_id="FS-001",
            location="Feeder 3B",
            fault_type="overvoltage",
            severity="minor",
            description="Temporary overvoltage spike",
        )
        assert fault.sensor_id == "FS-001"
        assert fault.voltage_drop is None
        assert fault.duration_ms is None
        assert fault.resolved is False  # Default value

    def test_fault_event_with_fault_id(self):
        """Test fault event with fault_id"""
        fault = FaultEvent(
            fault_id=123,
            timestamp=datetime.now(timezone.utc),
            sensor_id="FS-001",
            location="Feeder 3B",
            fault_type="ground_fault",
            severity="major",
            description="Ground fault detected",
        )
        assert fault.fault_id == 123

    def test_fault_event_missing_required_field(self):
        """Test fault event with missing required field"""
        data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc),
            "sensor_id": "FS-001",
            # Missing location
            "fault_type": "short_circuit",
            "severity": "critical",
            "description": "Test fault",
        }
        with pytest.raises(ValueError):
            FaultEvent(**data)

    def test_fault_event_default_resolved_false(self):
        """Test fault event default resolved value"""
        fault = FaultEvent(
            timestamp=datetime.now(timezone.utc),
            sensor_id="FS-001",
            location="Feeder 3B",
            fault_type="undervoltage",
            severity="minor",
            description="Temporary undervoltage",
        )
        assert fault.resolved is False

    def test_fault_event_various_fault_types(self):
        """Test fault events with different fault types"""
        fault_types = ["short_circuit", "ground_fault", "overvoltage", "undervoltage"]
        for fault_type in fault_types:
            fault = FaultEvent(
                timestamp=datetime.now(timezone.utc),
                sensor_id="FS-001",
                location="Feeder 3B",
                fault_type=fault_type,
                severity="critical",
                description=f"Testing {fault_type}",
            )
            assert fault.fault_type == fault_type

    def test_fault_event_various_severities(self):
        """Test fault events with different severities"""
        severities = ["critical", "major", "minor"]
        for severity in severities:
            fault = FaultEvent(
                timestamp=datetime.now(timezone.utc),
                sensor_id="FS-001",
                location="Feeder 3B",
                fault_type="short_circuit",
                severity=severity,
                description=f"Testing {severity} fault",
            )
            assert fault.severity == severity
