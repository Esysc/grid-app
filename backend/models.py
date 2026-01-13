"""
Pydantic models for grid monitoring data validation
"""

from datetime import datetime
from typing import Annotated, ClassVar, Optional

from pydantic import ConfigDict, Field
from pydantic.main import BaseModel  # explicit import helps type checkers


class SensorBase(BaseModel):
    sensor_id: Annotated[str, Field(..., description="Unique sensor identifier")]
    location: Annotated[str, Field(..., description="Grid location (e.g., 'Substation A')")]


class VoltageReading(SensorBase):
    """Voltage sensor reading"""

    timestamp: datetime
    voltage_l1: Annotated[float, Field(..., ge=0, le=500000, description="Line 1 voltage (V)")]
    voltage_l2: Annotated[float, Field(..., ge=0, le=500000, description="Line 2 voltage (V)")]
    voltage_l3: Annotated[float, Field(..., ge=0, le=500000, description="Line 3 voltage (V)")]
    frequency: Annotated[float, Field(..., ge=45, le=65, description="Frequency (Hz)")]

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sensor_id": "VS-001",
                "location": "Substation A",
                "timestamp": "2026-01-09T10:30:00Z",
                "voltage_l1": 230.5,
                "voltage_l2": 231.2,
                "voltage_l3": 229.8,
                "frequency": 50.0,
            }
        },
    )


class PowerQualityMetrics(SensorBase):
    """Power quality analysis metrics"""

    timestamp: datetime
    thd_voltage: float = Field(..., ge=0, le=100, description="Total Harmonic Distortion (%)")
    thd_current: float = Field(..., ge=0, le=100, description="Current THD (%)")
    power_factor: float = Field(..., ge=-1, le=1, description="Power factor")
    voltage_imbalance: float = Field(..., ge=0, le=100, description="Voltage imbalance (%)")
    flicker_severity: float = Field(..., ge=0, le=10, description="Flicker severity")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sensor_id": "PQ-001",
                "location": "Substation A",
                "timestamp": "2026-01-09T10:30:00Z",
                "thd_voltage": 2.5,
                "thd_current": 3.2,
                "power_factor": 0.95,
                "voltage_imbalance": 1.2,
                "flicker_severity": 0.8,
            }
        },
    )


class FaultEvent(BaseModel):
    """Grid fault event"""

    fault_id: Annotated[Optional[int], Field(default=None)] = None
    timestamp: Annotated[datetime, Field(...)]
    sensor_id: Annotated[str, Field(...)]
    location: Annotated[str, Field(...)]
    fault_type: Annotated[
        str, Field(..., description="Type: short_circuit, ground_fault, overvoltage, undervoltage")
    ]
    severity: Annotated[str, Field(..., description="Severity: critical, major, minor")]
    voltage_drop: Annotated[
        Optional[float], Field(default=None, description="Voltage drop (%)")
    ] = None
    duration_ms: Annotated[
        Optional[int], Field(default=None, description="Fault duration (ms)")
    ] = None
    resolved: Annotated[bool, Field(default=False)] = False
    description: Annotated[str, Field(...)]

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-09T10:32:15Z",
                "sensor_id": "FS-001",
                "location": "Feeder 3B",
                "fault_type": "short_circuit",
                "severity": "critical",
                "voltage_drop": 85.5,
                "duration_ms": 150,
                "resolved": True,
                "description": "Phase-to-ground short circuit detected",
            }
        },
    )


class SensorStats(BaseModel):
    """Aggregated sensor statistics"""

    total_sensors: int
    active_sensors: int
    offline_sensors: int
    avg_voltage: float
    avg_power_factor: float
    total_faults_24h: int
    quality_violations: int


class HealthCheck(BaseModel):
    """API health check response"""

    status: str
    timestamp: datetime
    database_connected: bool
    version: str = "1.0.0"


class SensorStatus(BaseModel):
    """Current sensor status from MQTT data"""

    sensor_id: str
    sensor_type: str  # 'voltage' or 'power_quality'
    location: str
    last_reading_timestamp: datetime
    is_operational: bool
    seconds_since_update: int
    latest_value: Optional[float] = None  # Latest voltage or power factor

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sensor_id": "VS-001",
                "sensor_type": "voltage",
                "location": "Substation A",
                "last_reading_timestamp": "2026-01-13T10:30:45.123Z",
                "is_operational": True,
                "seconds_since_update": 5,
                "latest_value": 230.5,
            }
        },
    )
