"""
Unit tests for data generator logic with mocked randomness
"""

import math
from unittest.mock import patch

from data_generator import GridDataGenerator
from models import FaultEvent, PowerQualityMetrics, VoltageReading


class TestGridDataGeneratorVoltage:
    """Test GridDataGenerator voltage reading generation"""

    def test_generate_voltage_reading_deterministic(self):
        """Test voltage reading with mocked random values"""
        generator = GridDataGenerator()

        with patch("random.gauss", return_value=0.0), patch("random.uniform", return_value=0.0):
            reading = generator.generate_voltage_reading(
                sensor_id="VS-001", location="Substation A"
            )

            assert reading.sensor_id == "VS-001"
            assert reading.location == "Substation A"
            assert math.isclose(reading.voltage_l1, 230.0)  # base_voltage + gauss(0) + uniform(0)
            assert math.isclose(reading.voltage_l2, 230.0)
            assert math.isclose(reading.voltage_l3, 230.0)
            assert math.isclose(reading.frequency, 50.0)  # base_frequency + uniform(0)

    def test_generate_voltage_reading_with_variations(self):
        """Test voltage reading with realistic variations"""
        generator = GridDataGenerator()

        with patch("random.gauss", return_value=2.5), patch(
            "random.uniform", side_effect=[0.5, -0.5, 0.2, 0.1]
        ):
            reading = generator.generate_voltage_reading(
                sensor_id="VS-002", location="Substation B"
            )

            assert math.isclose(reading.voltage_l1, 232.5 + 0.5)  # 230 + 2.5 + 0.5
            assert math.isclose(reading.voltage_l2, 232.5 - 0.5)  # 230 + 2.5 - 0.5
            assert math.isclose(reading.voltage_l3, 232.5 + 0.2)  # 230 + 2.5 + 0.2

    def test_generate_voltage_reading_random_sensor(self):
        """Test voltage reading with random sensor selection"""
        generator = GridDataGenerator()

        with patch("random.choice", return_value="VS-003"), patch(
            "random.gauss", return_value=0.0
        ), patch("random.uniform", return_value=0.0):
            reading = generator.generate_voltage_reading()

            assert reading.sensor_id == "VS-003"

    def test_generate_voltage_reading_frequency_range(self):
        """Test voltage reading with various frequency values"""
        generator = GridDataGenerator()

        with patch("random.gauss", return_value=0.0), patch(
            "random.uniform", side_effect=[0.0, 0.0, 0.0, 0.05]
        ):
            reading = generator.generate_voltage_reading(
                sensor_id="VS-001", location="Substation A"
            )

            assert math.isclose(reading.frequency, 50.05)


class TestGridDataGeneratorPowerQuality:
    """Test GridDataGenerator power quality metrics generation"""

    def test_generate_power_quality_normal_conditions(self):
        """Test power quality generation with normal conditions"""
        generator = GridDataGenerator()

        with patch("random.random", return_value=0.15):  # > 0.1, so normal
            with patch("random.uniform", side_effect=[2.0, 3.0, 0.95, 1.0, 0.8]):
                pq = generator.generate_power_quality(sensor_id="VS-001", location="Substation A")

                assert pq.sensor_id == "PQ-001"
                assert pq.location == "Substation A"
                assert math.isclose(pq.thd_voltage, 2.0)
                assert math.isclose(pq.thd_current, 3.0)
                assert math.isclose(pq.power_factor, 0.95)

    def test_generate_power_quality_violation_conditions(self):
        """Test power quality generation with violation conditions"""
        generator = GridDataGenerator()

        with patch("random.random", return_value=0.05):  # < 0.1, so violation
            with patch("random.uniform", side_effect=[8.0, 12.0, 0.75, 3.0, 2.5]):
                pq = generator.generate_power_quality(sensor_id="VS-002", location="Substation B")

                assert math.isclose(pq.thd_voltage, 8.0)
                assert math.isclose(pq.thd_current, 12.0)
                assert math.isclose(pq.power_factor, 0.75)
                assert math.isclose(pq.voltage_imbalance, 3.0)
                assert math.isclose(pq.flicker_severity, 2.5)

    def test_generate_power_quality_sensor_conversion(self):
        """Test VS sensor ID conversion to PQ"""
        generator = GridDataGenerator()

        with patch("random.random", return_value=0.15), patch(
            "random.uniform", side_effect=[2.0, 3.0, 0.95, 1.0, 0.8]
        ):
            pq = generator.generate_power_quality(sensor_id="VS-002", location="Substation B")

            assert pq.sensor_id == "PQ-002"

    def test_generate_power_quality_random_location(self):
        """Test power quality with random location selection"""
        generator = GridDataGenerator()

        with patch("random.random", return_value=0.15), patch(
            "random.uniform", side_effect=[2.0, 3.0, 0.95, 1.0, 0.8]
        ), patch("random.choice", return_value="Feeder 5A"):
            pq = generator.generate_power_quality(sensor_id="PQ-003")

            assert pq.location == "Feeder 5A"


class TestGridDataGeneratorFault:
    """Test GridDataGenerator fault event generation"""

    def test_generate_fault_event_creates_valid_object(self):
        """Test that fault event generation creates a valid FaultEvent"""
        generator = GridDataGenerator()
        fault = generator.generate_fault_event()

        assert isinstance(fault, FaultEvent)
        assert fault.fault_type in generator.FAULT_TYPES
        assert fault.severity in generator.SEVERITIES
        assert fault.sensor_id is not None
        assert fault.location in generator.LOCATIONS

    def test_generate_fault_event_voltage_drop_ranges(self):
        """Test that voltage drop is within expected ranges for severity"""
        generator = GridDataGenerator()

        for _ in range(10):
            fault = generator.generate_fault_event()
            assert fault.voltage_drop is not None

            if fault.severity == "critical":
                assert 70 <= fault.voltage_drop <= 100
            elif fault.severity == "major":
                assert 40 <= fault.voltage_drop <= 70
            elif fault.severity == "minor":
                assert 10 <= fault.voltage_drop <= 40

    def test_generate_fault_event_duration_within_limits(self):
        """Test that duration is within expected ranges"""
        generator = GridDataGenerator()

        for _ in range(10):
            fault = generator.generate_fault_event()
            assert fault.duration_ms is not None

            if fault.fault_type == "short_circuit":
                assert 50 <= fault.duration_ms <= 200
            elif fault.fault_type == "ground_fault":
                assert 100 <= fault.duration_ms <= 500
            elif fault.fault_type == "overvoltage":
                assert 200 <= fault.duration_ms <= 1000
            elif fault.fault_type == "undervoltage":
                assert 500 <= fault.duration_ms <= 2000

    def test_generate_fault_event_resolved_distribution(self):
        """Test that resolved status follows expected distribution"""
        generator = GridDataGenerator()
        resolved_count = 0
        total_tests = 100

        for _ in range(total_tests):
            fault = generator.generate_fault_event()
            if fault.resolved:
                resolved_count += 1

        # Approximately 85% should be resolved (with some tolerance)
        resolved_percentage = (resolved_count / total_tests) * 100
        assert 70 < resolved_percentage < 95  # Allow reasonable variance

    def test_generate_fault_event_has_description(self):
        """Test that fault events have descriptions"""
        generator = GridDataGenerator()

        for _ in range(5):
            fault = generator.generate_fault_event()
            assert fault.description is not None
            assert len(fault.description) > 0


class TestGridDataGeneratorConstants:
    """Test GridDataGenerator constants and initialization"""

    def test_generator_sensor_ids(self):
        """Test generator has correct sensor IDs"""
        generator = GridDataGenerator()
        assert "VS-001" in generator.SENSOR_IDS
        assert "VS-002" in generator.SENSOR_IDS
        assert "VS-003" in generator.SENSOR_IDS
        assert "VS-004" in generator.SENSOR_IDS

    def test_generator_locations(self):
        """Test generator has correct locations"""
        generator = GridDataGenerator()
        assert "Substation A" in generator.LOCATIONS
        assert "Substation B" in generator.LOCATIONS
        assert "Feeder 3B" in generator.LOCATIONS
        assert "Feeder 5A" in generator.LOCATIONS

    def test_generator_fault_types(self):
        """Test generator has correct fault types"""
        generator = GridDataGenerator()
        assert "short_circuit" in generator.FAULT_TYPES
        assert "ground_fault" in generator.FAULT_TYPES
        assert "overvoltage" in generator.FAULT_TYPES
        assert "undervoltage" in generator.FAULT_TYPES

    def test_generator_base_values(self):
        """Test generator base values"""
        generator = GridDataGenerator()
        assert math.isclose(generator.base_voltage, 230.0)
        assert math.isclose(generator.base_frequency, 50.0)


class TestGridDataGeneratorHistorical:
    """Test GridDataGenerator historical data generation"""

    def test_generate_historical_data_default(self):
        """Test historical data generation with default parameters"""
        generator = GridDataGenerator()
        voltage_readings, power_quality, fault_events = generator.generate_historical_data()

        assert len(voltage_readings) > 0
        assert len(power_quality) > 0
        assert len(fault_events) > 0
        assert all(isinstance(v, VoltageReading) for v in voltage_readings)
        assert all(isinstance(p, PowerQualityMetrics) for p in power_quality)
        assert all(isinstance(f, FaultEvent) for f in fault_events)

    def test_generate_historical_data_one_hour(self):
        """Test historical data generation for 1 hour"""
        generator = GridDataGenerator()
        voltage_readings, power_quality, fault_events = generator.generate_historical_data(
            hours=1, interval_minutes=5
        )

        # 1 hour = 60 minutes, 5 minute intervals = 12 intervals
        # 4 sensors per interval = 48 readings
        assert len(voltage_readings) == 48
        assert len(power_quality) == 48
        assert len(fault_events) > 0

    def test_generate_historical_data_custom_interval(self):
        """Test historical data generation with custom interval"""
        generator = GridDataGenerator()
        voltage_readings, power_quality, _ = generator.generate_historical_data(
            hours=2, interval_minutes=10
        )

        # 2 hours = 120 minutes, 10 minute intervals = 12 intervals
        # 4 sensors per interval = 48 readings
        assert len(voltage_readings) == 48
        assert len(power_quality) == 48

    def test_generate_historical_data_voltage_validity(self):
        """Test that generated historical voltage readings are valid"""
        generator = GridDataGenerator()
        voltage_readings, _, _ = generator.generate_historical_data(hours=1, interval_minutes=15)

        for reading in voltage_readings:
            assert 0 <= reading.voltage_l1 <= 500000
            assert 0 <= reading.voltage_l2 <= 500000
            assert 0 <= reading.voltage_l3 <= 500000
            assert 45 <= reading.frequency <= 65
            assert reading.sensor_id.startswith("VS-")
            assert reading.location in generator.LOCATIONS

    def test_generate_historical_data_power_quality_validity(self):
        """Test that generated historical power quality metrics are valid"""
        generator = GridDataGenerator()
        _, power_quality, _ = generator.generate_historical_data(hours=1, interval_minutes=15)

        for pq in power_quality:
            assert 0 <= pq.thd_voltage <= 100
            assert 0 <= pq.thd_current <= 100
            assert -1 <= pq.power_factor <= 1
            assert 0 <= pq.voltage_imbalance <= 100
            assert 0 <= pq.flicker_severity <= 10
            assert pq.sensor_id.startswith("PQ-")
            assert pq.location in generator.LOCATIONS

    def test_generate_historical_data_fault_validity(self):
        """Test that generated historical fault events are valid"""
        generator = GridDataGenerator()
        _, _, fault_events = generator.generate_historical_data(hours=1)

        for fault in fault_events:
            assert fault.fault_type in generator.FAULT_TYPES
            assert fault.severity in generator.SEVERITIES
            assert fault.location in generator.LOCATIONS
            assert isinstance(fault.description, str)
            assert len(fault.description) > 0

    def test_generate_historical_data_timestamps_ordered(self):
        """Test that generated voltage readings have ordered timestamps"""
        generator = GridDataGenerator()
        voltage_readings, _, _ = generator.generate_historical_data(hours=2, interval_minutes=30)

        # Group by sensor and check timestamps are in order
        readings_by_sensor: dict[str, list[VoltageReading]] = {}
        for reading in voltage_readings:
            if reading.sensor_id not in readings_by_sensor:
                readings_by_sensor[reading.sensor_id] = []
            readings_by_sensor[reading.sensor_id].append(reading)

        for sensor_readings in readings_by_sensor.values():
            timestamps = [r.timestamp for r in sensor_readings]
            assert timestamps == sorted(timestamps)
