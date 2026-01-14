"""
GraphQL schema for Grid Monitoring API
"""

# pylint: disable=not-callable,too-many-positional-arguments,redefined-builtin
# SQLAlchemy func creates callables dynamically, and Strawberry types need many fields

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import strawberry
from database import FaultEventDB, PowerQualityDB, VoltageReadingDB
from sqlalchemy import Float, Select
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

# ==============================================================================
# STEP 1: ENHANCED OUTPUT TYPES WITH COMPLETE DATA
# ==============================================================================


@strawberry.type
class VoltageReading:
    """Voltage reading with all three phases"""

    id: int
    sensor_id: str
    location: str
    voltage_l1: float
    voltage_l2: float
    voltage_l3: float
    frequency: float
    timestamp: datetime

    def __init__(
        self,
        id: int,
        sensor_id: str,
        location: str,
        voltage_l1: float,
        voltage_l2: float,
        voltage_l3: float,
        frequency: float,
        timestamp: datetime,
    ) -> None:  # pylint: disable=redefined-builtin
        self.id = id
        self.sensor_id = sensor_id
        self.location = location
        self.voltage_l1 = voltage_l1
        self.voltage_l2 = voltage_l2
        self.voltage_l3 = voltage_l3
        self.frequency = frequency
        self.timestamp = timestamp


@strawberry.type
class PowerQuality:
    """Complete power quality metrics"""

    id: int
    sensor_id: str
    location: str
    thd_voltage: float
    thd_current: float
    power_factor: float
    voltage_imbalance: float
    flicker_severity: float
    timestamp: datetime

    def __init__(
        self,
        id: int,
        sensor_id: str,
        location: str,
        thd_voltage: float,
        thd_current: float,
        power_factor: float,
        voltage_imbalance: float,
        flicker_severity: float,
        timestamp: datetime,
    ) -> None:  # pylint: disable=redefined-builtin
        self.id = id
        self.sensor_id = sensor_id
        self.location = location
        self.thd_voltage = thd_voltage
        self.thd_current = thd_current
        self.power_factor = power_factor
        self.voltage_imbalance = voltage_imbalance
        self.flicker_severity = flicker_severity
        self.timestamp = timestamp


@strawberry.type
class FaultEvent:
    """Fault event with precise timing"""

    id: int
    event_id: str
    severity: str
    event_type: str
    location: str
    timestamp: datetime
    duration_ms: int
    resolved: bool
    resolved_at: Optional[datetime]

    def __init__(
        self,
        id: int,
        event_id: str,
        severity: str,
        event_type: str,
        location: str,
        timestamp: datetime,
        duration_ms: int,
        resolved: bool,
        resolved_at: Optional[datetime],
    ) -> None:  # pylint: disable=redefined-builtin
        self.id = id
        self.event_id = event_id
        self.severity = severity
        self.event_type = event_type
        self.location = location
        self.timestamp = timestamp
        self.duration_ms = duration_ms
        self.resolved = resolved
        self.resolved_at = resolved_at


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

    def __init__(
        self,
        total_sensors: int,
        active_sensors: int,
        fault_count_24h: int,
        violation_count_24h: int,
        avg_voltage: float,
        min_voltage: float,
        max_voltage: float,
    ) -> None:
        self.total_sensors = total_sensors
        self.active_sensors = active_sensors
        self.fault_count_24h = fault_count_24h
        self.violation_count_24h = violation_count_24h
        self.avg_voltage = avg_voltage
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage


# ==============================================================================
# STEP 2: INPUT TYPES FOR MUTATIONS
# ==============================================================================


@strawberry.input
class VoltageReadingInput:
    """Input type for voltage readings"""

    sensor_id: str
    location: str
    voltage_l1: float
    voltage_l2: float
    voltage_l3: float
    frequency: float
    timestamp: datetime


@strawberry.input
class PowerQualityInput:
    """Input type for power quality data"""

    sensor_id: str
    location: str
    thd_voltage: float
    thd_current: float
    power_factor: float
    voltage_imbalance: float
    flicker_severity: float
    timestamp: datetime


@strawberry.input
class FaultEventInput:
    """Input type for fault events"""

    event_id: str
    severity: str
    event_type: str
    location: str
    timestamp: datetime
    duration_ms: int


# ==============================================================================
# STEP 3: RESPONSE TYPES FOR MUTATIONS
# ==============================================================================


@strawberry.type
class MutationResult:
    """Generic mutation result"""

    success: bool
    message: str
    id: Optional[int] = None

    def __init__(
        self, success: bool, message: str, id: Optional[int] = None
    ) -> None:  # pylint: disable=redefined-builtin
        self.success = success
        self.message = message
        self.id = id


# ==============================================================================
# QUERIES WITH COMPLETE DATA AND ADVANCED FILTERING
# ==============================================================================


@strawberry.type
class Query:
    """GraphQL Query root type"""

    @strawberry.field
    def hello(self, name: str = "World") -> str:
        """Hello world query"""
        return f"Hello {name}!"

    @strawberry.field
    async def voltage_readings(
        self,
        info: Info[Any, Any],
        limit: int = 10,
        sensor_id: Optional[str] = None,
        hours: int = 24,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[VoltageReading]:
        """Get voltage readings with optional filtering by time range and sensor"""
        db: AsyncSession = info.context["db"]

        # Build query with time filtering
        query = select(VoltageReadingDB).order_by(VoltageReadingDB.timestamp.desc())

        # Apply time range filter
        if start_date is not None and end_date is not None:
            query = query.where(
                (VoltageReadingDB.timestamp >= start_date)
                & (VoltageReadingDB.timestamp <= end_date)
            )
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.where(VoltageReadingDB.timestamp >= cutoff_time)

        # Apply sensor filter
        if sensor_id:
            query = query.where(VoltageReadingDB.sensor_id == sensor_id)

        query = query.limit(limit)

        result = await db.execute(query)
        readings: List[VoltageReading] = []
        for row in result.scalars():
            reading = VoltageReading(
                id=row.id,
                sensor_id=row.sensor_id,
                location=row.location,
                voltage_l1=row.voltage_l1,
                voltage_l2=row.voltage_l2,
                voltage_l3=row.voltage_l3,
                frequency=row.frequency,
                timestamp=row.timestamp,
            )
            readings.append(reading)
        return readings

    @strawberry.field
    async def power_quality(
        self,
        info: Info[Any, Any],
        limit: int = 10,
        sensor_id: Optional[str] = None,
        hours: int = 24,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[PowerQuality]:
        """Get power quality data with optional filtering"""
        db: AsyncSession = info.context["db"]

        # Build query with time filtering
        query = select(PowerQualityDB).order_by(PowerQualityDB.timestamp.desc())

        # Apply time range filter
        if start_date is not None and end_date is not None:
            query = query.where(
                (PowerQualityDB.timestamp >= start_date) & (PowerQualityDB.timestamp <= end_date)
            )
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.where(PowerQualityDB.timestamp >= cutoff_time)

        # Apply sensor filter
        if sensor_id:
            query = query.where(PowerQualityDB.sensor_id == sensor_id)

        query = query.limit(limit)

        result = await db.execute(query)
        pqs: List[PowerQuality] = []
        for row in result.scalars():
            pq = PowerQuality(
                id=row.id,
                sensor_id=row.sensor_id,
                location=row.location,
                thd_voltage=row.thd_voltage,
                thd_current=row.thd_current,
                power_factor=row.power_factor,
                voltage_imbalance=row.voltage_imbalance,
                flicker_severity=row.flicker_severity,
                timestamp=row.timestamp,
            )
            pqs.append(pq)
        return pqs

    @strawberry.field
    async def fault_events(
        self,
        info: Info[Any, Any],
        limit: int = 10,
        severity: Optional[str] = None,
        hours: int = 24,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[FaultEvent]:
        """Get fault events with optional filtering by severity and time range"""
        db: AsyncSession = info.context["db"]

        query = select(FaultEventDB).order_by(FaultEventDB.timestamp.desc())

        # Apply time range filter
        if start_date is not None and end_date is not None:
            query = query.where(
                (FaultEventDB.timestamp >= start_date) & (FaultEventDB.timestamp <= end_date)
            )
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.where(FaultEventDB.timestamp >= cutoff_time)

        # Apply severity filter
        if severity:
            query = query.where(FaultEventDB.severity == severity)

        query = query.limit(limit)

        result = await db.execute(query)
        faults: List[FaultEvent] = []
        for row in result.scalars():
            fault = FaultEvent(
                id=row.id,
                event_id=f"EVT-{row.id}",
                severity=row.severity,
                event_type=row.fault_type,
                location=row.location,
                timestamp=row.timestamp,
                duration_ms=row.duration_ms or 0,
                resolved=row.resolved or False,
                resolved_at=row.timestamp if row.resolved else None,
            )
            faults.append(fault)
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

        return SensorStats(
            total_sensors=total_sensors,
            active_sensors=active_sensors,
            fault_count_24h=fault_count_24h,
            violation_count_24h=violation_count_24h,
            avg_voltage=avg_voltage,
            min_voltage=min_voltage,
            max_voltage=max_voltage,
        )


# ==============================================================================
# MUTATIONS FOR DATA INGESTION
# ==============================================================================


@strawberry.type
class Mutation:
    """GraphQL Mutation root type"""

    @strawberry.mutation
    async def ingest_voltage_reading(
        self, info: Info[Any, Any], reading: VoltageReadingInput
    ) -> MutationResult:
        """Ingest a new voltage reading"""
        db: AsyncSession = info.context["db"]
        try:
            db_reading = VoltageReadingDB(
                timestamp=reading.timestamp,
                sensor_id=reading.sensor_id,
                location=reading.location,
                voltage_l1=reading.voltage_l1,
                voltage_l2=reading.voltage_l2,
                voltage_l3=reading.voltage_l3,
                frequency=reading.frequency,
            )
            db.add(db_reading)
            await db.commit()
            await db.refresh(db_reading)
            return MutationResult(
                success=True, message="Voltage reading ingested", id=db_reading.id
            )
        except Exception as error:  # pylint: disable=broad-except
            await db.rollback()
            return MutationResult(success=False, message=f"Error: {str(error)}")

    @strawberry.mutation
    async def ingest_power_quality(
        self, info: Info[Any, Any], data: PowerQualityInput
    ) -> MutationResult:
        """Ingest new power quality data"""
        db: AsyncSession = info.context["db"]
        try:
            db_pq = PowerQualityDB(
                timestamp=data.timestamp,
                sensor_id=data.sensor_id,
                location=data.location,
                thd_voltage=data.thd_voltage,
                thd_current=data.thd_current,
                power_factor=data.power_factor,
                voltage_imbalance=data.voltage_imbalance,
                flicker_severity=data.flicker_severity,
            )
            db.add(db_pq)
            await db.commit()
            await db.refresh(db_pq)
            return MutationResult(success=True, message="Power quality data ingested", id=db_pq.id)
        except Exception as error:  # pylint: disable=broad-except
            await db.rollback()
            return MutationResult(success=False, message=f"Error: {str(error)}")

    @strawberry.mutation
    async def create_fault_event(
        self, info: Info[Any, Any], event: FaultEventInput
    ) -> MutationResult:
        """Create a new fault event"""
        db: AsyncSession = info.context["db"]
        try:
            db_fault = FaultEventDB(
                event_id=event.event_id,
                severity=event.severity,
                fault_type=event.event_type,
                location=event.location,
                timestamp=event.timestamp,
                duration_ms=event.duration_ms,
                resolved=False,
            )
            db.add(db_fault)
            await db.commit()
            await db.refresh(db_fault)
            return MutationResult(success=True, message="Fault event created", id=db_fault.id)
        except Exception as error:  # pylint: disable=broad-except
            await db.rollback()
            return MutationResult(success=False, message=f"Error: {str(error)}")


# ==============================================================================
# SUBSCRIPTIONS FOR REAL-TIME UPDATES
# ==============================================================================


@strawberry.type
class Subscription:
    """GraphQL Subscription root type for real-time updates"""

    @strawberry.subscription
    async def voltage_reading_updated(
        self, sensor_id: Optional[str] = None
    ) -> Any:  # Returns AsyncGenerator[VoltageReading, None]
        """Subscribe to voltage reading updates"""
        # Note: This requires WebSocket connection and event streaming infrastructure
        # Implementation requires message queue or event bus (Redis, RabbitMQ, etc.)
        # For now, provide generator structure that can be connected to MQTT/Redis
        try:
            # Placeholder: In production, subscribe to message queue
            # Example pattern:
            # async for message in event_bus.subscribe('voltage_readings'):
            #     if sensor_id is None or message.sensor_id == sensor_id:
            #         yield message
            yield VoltageReading(
                id=0,
                sensor_id=sensor_id or "unknown",
                location="pending",
                voltage_l1=0.0,
                voltage_l2=0.0,
                voltage_l3=0.0,
                frequency=50.0,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception:  # pylint: disable=broad-except
            pass

    @strawberry.subscription
    async def power_quality_updated(
        self, sensor_id: Optional[str] = None
    ) -> Any:  # Returns AsyncGenerator[PowerQuality, None]
        """Subscribe to power quality updates"""
        # Note: This requires WebSocket connection and event streaming infrastructure
        # Implementation requires message queue or event bus (Redis, RabbitMQ, etc.)
        try:
            # Placeholder: In production, subscribe to message queue
            yield PowerQuality(
                id=0,
                sensor_id=sensor_id or "unknown",
                location="pending",
                thd_voltage=0.0,
                thd_current=0.0,
                power_factor=1.0,
                voltage_imbalance=0.0,
                flicker_severity=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception:  # pylint: disable=broad-except
            pass

    @strawberry.subscription
    async def fault_occurred(
        self, severity: Optional[str] = None
    ) -> Any:  # Returns AsyncGenerator[FaultEvent, None]
        """Subscribe to fault event notifications"""
        # Note: This requires WebSocket connection and event streaming infrastructure
        # Implementation requires message queue or event bus (Redis, RabbitMQ, etc.)
        try:
            # Placeholder: In production, subscribe to message queue
            yield FaultEvent(
                id=0,
                event_id="EVT-0",
                severity=severity or "unknown",
                event_type="unknown",
                location="pending",
                timestamp=datetime.now(timezone.utc),
                duration_ms=0,
                resolved=False,
                resolved_at=None,
            )
        except Exception:  # pylint: disable=broad-except
            pass


# ==============================================================================
# SCHEMA CREATION WITH QUERIES, MUTATIONS, AND SUBSCRIPTIONS
# ==============================================================================

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
