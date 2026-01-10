"""
GraphQL schema for Grid Monitoring API
"""

# pylint: disable=not-callable  # SQLAlchemy func creates callables dynamically

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import strawberry
from database import FaultEventDB, PowerQualityDB, VoltageReadingDB
from sqlalchemy import Float, Select
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info


@strawberry.type
class VoltageReading:
    """Voltage reading type"""

    id: int
    sensor_id: str
    voltage: float
    timestamp: datetime
    location: str


@strawberry.type
class PowerQuality:
    """Power quality type"""

    id: int
    sensor_id: str
    thd: float
    frequency: float
    timestamp: datetime


@strawberry.type
class FaultEvent:
    """Fault event type"""

    id: int
    event_id: str
    severity: str
    event_type: str
    location: str
    timestamp: datetime
    duration_seconds: int
    resolved_at: Optional[datetime]


@strawberry.type
class SensorStats:
    """Sensor statistics type"""

    total_sensors: int
    active_sensors: int
    fault_count_24h: int
    violation_count_24h: int
    avg_voltage: float
    min_voltage: float
    max_voltage: float


@strawberry.type
class Query:
    """GraphQL Query root type"""

    @strawberry.field
    def hello(self, name: str = "World") -> str:
        """Hello world query"""
        return f"Hello {name}!"

    @strawberry.field
    async def voltage_readings(
        self, info: Info[Any, Any], limit: int = 10, sensor_id: Optional[str] = None
    ) -> List[VoltageReading]:
        """Get voltage readings from database"""
        db: AsyncSession = info.context["db"]
        query = select(VoltageReadingDB).order_by(VoltageReadingDB.timestamp.desc()).limit(limit)
        if sensor_id:
            query = query.where(VoltageReadingDB.sensor_id == sensor_id)
        result = await db.execute(query)
        readings: List[VoltageReading] = []
        for row in result.scalars():
            readings.append(
                VoltageReading(  # type: ignore[call-arg]
                    id=row.id,
                    sensor_id=row.sensor_id,
                    voltage=row.voltage_l1,
                    timestamp=row.timestamp,
                    location=row.location,
                )
            )
        return readings

    @strawberry.field
    async def power_quality(self, info: Info[Any, Any], limit: int = 10) -> List[PowerQuality]:
        """Get power quality data from database"""
        db: AsyncSession = info.context["db"]
        query = select(PowerQualityDB).order_by(PowerQualityDB.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        pqs: List[PowerQuality] = []
        for row in result.scalars():
            pqs.append(
                PowerQuality(  # type: ignore[call-arg]
                    id=row.id,
                    sensor_id=row.sensor_id,
                    thd=row.thd_voltage,
                    frequency=50.0,  # Standard European grid frequency
                    timestamp=row.timestamp,
                )
            )
        return pqs

    @strawberry.field
    async def recent_faults(self, info: Info[Any, Any], limit: int = 10) -> List[FaultEvent]:
        """Get recent fault events from database"""
        db: AsyncSession = info.context["db"]
        query = select(FaultEventDB).order_by(FaultEventDB.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        faults: List[FaultEvent] = []
        for row in result.scalars():
            faults.append(
                FaultEvent(  # type: ignore[call-arg]
                    id=row.id,
                    event_id=f"EVT-{row.id}",  # Generate event ID from database ID
                    severity=row.severity,
                    event_type=row.fault_type,
                    location=row.location,
                    timestamp=row.timestamp,
                    duration_seconds=(row.duration_ms or 0) // 1000,  # Convert ms to seconds
                    resolved_at=row.timestamp if row.resolved else None,
                )
            )
        return faults

    @strawberry.field
    async def sensor_stats(self, info: Info[Any, Any]) -> SensorStats:
        """Get sensor statistics from database"""
        db: AsyncSession = info.context["db"]

        # Get unique sensor count
        total_query = select(
            sa_func.count(
                sa_func.distinct(VoltageReadingDB.sensor_id)
            )  # pylint: disable=not-callable
        )
        total_result = await db.execute(total_query)
        total_sensors = total_result.scalar() or 0

        # Get active sensors (readings in last hour)
        time_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        active_query = select(
            sa_func.count(
                sa_func.distinct(VoltageReadingDB.sensor_id)
            )  # pylint: disable=not-callable
        ).where(VoltageReadingDB.timestamp >= time_cutoff)
        active_result = await db.execute(active_query)
        active_sensors = active_result.scalar() or 0

        # Get fault count (last 24h)
        fault_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        fault_query = select(sa_func.count(FaultEventDB.id)).where(  # pylint: disable=not-callable
            FaultEventDB.timestamp >= fault_cutoff
        )
        fault_result = await db.execute(fault_query)
        fault_count_24h = fault_result.scalar() or 0

        # Get voltage stats
        voltage_query: Select[tuple[float | None, float | None, float | None]] = select(
            sa_func.avg(VoltageReadingDB.voltage_l1).cast(Float),
            sa_func.min(VoltageReadingDB.voltage_l1).cast(Float),
            sa_func.max(VoltageReadingDB.voltage_l1).cast(Float),
        )
        voltage_result = await db.execute(voltage_query)
        voltage_row = voltage_result.one()
        avg_voltage = float(voltage_row[0]) if voltage_row[0] is not None else 0.0
        min_voltage = float(voltage_row[1]) if voltage_row[1] is not None else 0.0
        max_voltage = float(voltage_row[2]) if voltage_row[2] is not None else 0.0

        # Count voltage violations (last 24h)
        violation_query = select(
            sa_func.count(VoltageReadingDB.id)  # pylint: disable=not-callable
        ).where(
            VoltageReadingDB.timestamp >= fault_cutoff,
            (VoltageReadingDB.voltage_l1 < 207.0) | (VoltageReadingDB.voltage_l1 > 253.0),
        )
        violation_result = await db.execute(violation_query)
        violation_count_24h = violation_result.scalar() or 0

        return SensorStats(  # type: ignore[call-arg]
            total_sensors=total_sensors,
            active_sensors=active_sensors,
            fault_count_24h=fault_count_24h,
            violation_count_24h=violation_count_24h,
            avg_voltage=avg_voltage,
            min_voltage=min_voltage,
            max_voltage=max_voltage,
        )


schema = strawberry.Schema(query=Query)
