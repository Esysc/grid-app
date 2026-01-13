"""
Grid sensor data generator for realistic demo data
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from models import FaultEvent, PowerQualityMetrics, VoltageReading


class GridDataGenerator:
    """Generate realistic grid monitoring data"""

    SENSOR_IDS = [
        "VS-001",
        "VS-002",
        "VS-003",
        "VS-004",
        "VS-005",
        "VS-006",
        "VS-007",
    ]
    LOCATIONS = [
        "Substation A",
        "Substation B",
        "Feeder 3B",
        "Feeder 5A",
        "Feeder 1",
        "Transformer 1",
        "Transformer 2",
    ]
    FAULT_TYPES = ["short_circuit", "ground_fault", "overvoltage", "undervoltage"]
    SEVERITIES = ["critical", "major", "minor"]

    def __init__(self) -> None:
        self.base_voltage = 230.0  # Base voltage in V
        self.base_frequency = 50.0  # Base frequency in Hz

    def generate_voltage_reading(
        self, sensor_id: Optional[str] = None, location: Optional[str] = None
    ) -> VoltageReading:
        """Generate realistic voltage reading with slight variations"""
        if sensor_id is None:
            sensor_id = random.choice(self.SENSOR_IDS)
        if location is None:
            location = random.choice(self.LOCATIONS)

        # Add realistic variations
        voltage_variation = random.gauss(0, 2.5)  # ±2.5V standard deviation

        return VoltageReading(
            sensor_id=sensor_id,
            location=location,
            timestamp=datetime.now(timezone.utc),
            voltage_l1=self.base_voltage + voltage_variation + random.uniform(-1, 1),
            voltage_l2=self.base_voltage + voltage_variation + random.uniform(-1, 1),
            voltage_l3=self.base_voltage + voltage_variation + random.uniform(-1, 1),
            frequency=self.base_frequency + random.uniform(-0.1, 0.1),
        )

    def generate_power_quality(
        self, sensor_id: Optional[str] = None, location: Optional[str] = None
    ) -> PowerQualityMetrics:
        """Generate power quality metrics with occasional violations"""
        # Normalize sensor id: convert VS-xxx to PQ-xxx, or choose a random PQ id if not provided
        if sensor_id and sensor_id.startswith("VS-"):
            sensor_id = "PQ-" + sensor_id.split("-")[1]
        elif not sensor_id:
            sensor_id = "PQ-" + random.choice(["001", "002", "003", "004", "005", "006", "007"])
        if location is None:
            location = random.choice(self.LOCATIONS)

        # Occasional power quality issues (10% chance)
        is_violation = random.random() < 0.1

        if is_violation:
            thd_voltage = random.uniform(5.0, 12.0)  # Higher THD
            thd_current = random.uniform(8.0, 15.0)
            power_factor = random.uniform(0.70, 0.85)
            voltage_imbalance = random.uniform(2.5, 5.0)
            flicker_severity = random.uniform(1.5, 3.5)
        else:
            thd_voltage = random.uniform(1.0, 4.0)  # Normal THD
            thd_current = random.uniform(1.5, 5.0)
            power_factor = random.uniform(0.92, 0.99)
            voltage_imbalance = random.uniform(0.5, 2.0)
            flicker_severity = random.uniform(0.3, 1.2)

        return PowerQualityMetrics(
            sensor_id=sensor_id,
            location=location,
            timestamp=datetime.now(timezone.utc),
            thd_voltage=thd_voltage,
            thd_current=thd_current,
            power_factor=power_factor,
            voltage_imbalance=voltage_imbalance,
            flicker_severity=flicker_severity,
        )

    def generate_fault_event(self) -> FaultEvent:
        """Generate random fault event"""
        fault_type = random.choice(self.FAULT_TYPES)
        severity = random.choices(
            self.SEVERITIES, weights=[0.1, 0.3, 0.6]  # More minor faults than critical
        )[0]

        # Voltage drop based on severity
        voltage_drop_ranges = {"critical": (70, 100), "major": (40, 70), "minor": (10, 40)}
        voltage_drop = random.uniform(*voltage_drop_ranges[severity])

        # Duration based on fault type
        duration_ranges = {
            "short_circuit": (50, 200),
            "ground_fault": (100, 500),
            "overvoltage": (200, 1000),
            "undervoltage": (500, 2000),
        }
        duration = random.randint(*duration_ranges[fault_type])

        descriptions = {
            "short_circuit": (
                "Phase-to-ground short circuit detected on " f"{random.choice(['L1', 'L2', 'L3'])}"
            ),
            "ground_fault": "Ground fault with high earth current detected",
            "overvoltage": f"Overvoltage event: {random.randint(250, 280)}V sustained",
            "undervoltage": f"Undervoltage sag: {random.randint(180, 210)}V detected",
        }

        return FaultEvent(
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 86400)),
            sensor_id=random.choice([f"FS-{i:03d}" for i in range(1, 6)]),
            location=random.choice(self.LOCATIONS),
            fault_type=fault_type,
            severity=severity,
            voltage_drop=voltage_drop,
            duration_ms=duration,
            resolved=random.random() < 0.85,  # 85% resolved
            description=descriptions[fault_type],
        )

    def generate_historical_data(
        self, hours: int = 24, interval_minutes: int = 5
    ) -> Tuple[List[VoltageReading], List[PowerQualityMetrics], List[FaultEvent]]:
        """Generate historical data for the past N hours"""
        voltage_readings: List[VoltageReading] = []
        power_quality: List[PowerQualityMetrics] = []
        fault_events: List[FaultEvent] = []

        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        intervals = (hours * 60) // interval_minutes

        for i in range(intervals):
            timestamp = start_time + timedelta(minutes=i * interval_minutes)

            # Generate readings for each sensor
            for sensor_id, location in zip(self.SENSOR_IDS, self.LOCATIONS):
                voltage = self.generate_voltage_reading(sensor_id, location)
                voltage.timestamp = timestamp
                voltage_readings.append(voltage)

                pq = self.generate_power_quality(f"PQ-{sensor_id.split('-')[1]}", location)
                pq.timestamp = timestamp
                power_quality.append(pq)

        # Generate random fault events (5-15 per day)
        num_faults = random.randint(5, 15)
        for _ in range(num_faults):
            fault = self.generate_fault_event()
            fault_events.append(fault)

        return voltage_readings, power_quality, fault_events
