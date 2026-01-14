"""
GraphQL schema for Grid Monitoring API
"""

# pylint: disable=not-callable  # SQLAlchemy func creates callables dynamically

from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, List, Optional, cast

import strawberry
from sqlalchemy import Float, Select
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from database import FaultEventDB, PowerQualityDB, VoltageReadingDB


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


@strawberry.type
class SensorStats:
    """Sensor statistics type"""

    total_sensors: int
    active_sensors: int
    offline_sensors: int
    fault_count_24h: int
    violation_count_24h: int
    avg_voltage: float
    avg_power_factor: float
    min_voltage: float
    max_voltage: float


# ==============================================================================
# STEP 2: INPUT TYPES FOR MUTATIONS
# ==============================================================================


@strawberry.input
class TimeRangeFilter:
    """Filter for time-based queries"""

    hours: int = 24
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@strawberry.input
class VoltageReadingFilter:
    """Filter for voltage reading queries"""

    sensor_id: Optional[str] = None
    time_range: Optional[TimeRangeFilter] = None
    limit: int = 10


@strawberry.input
class PowerQualityFilter:
    """Filter for power quality queries"""

    sensor_id: Optional[str] = None
    time_range: Optional[TimeRangeFilter] = None
    limit: int = 10


@strawberry.input
class FaultEventFilter:
    """Filter for fault event queries"""

    severity: Optional[str] = None
    time_range: Optional[TimeRangeFilter] = None
    limit: int = 10


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
        self, info: Info[Any, Any], options: VoltageReadingFilter
    ) -> List[VoltageReading]:
        """Get voltage readings with optional filtering by time range and sensor"""
        db: AsyncSession = info.context["db"]

        # Build query with time filtering
        query = select(VoltageReadingDB).order_by(VoltageReadingDB.timestamp.desc())

        # Apply time range filter
        if options.time_range:
            if (
                options.time_range.start_date is not None
                and options.time_range.end_date is not None
            ):
                query = query.where(
                    (VoltageReadingDB.timestamp >= options.time_range.start_date)
                    & (VoltageReadingDB.timestamp <= options.time_range.end_date)
                )
            else:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=options.time_range.hours)
                query = query.where(VoltageReadingDB.timestamp >= cutoff_time)
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            query = query.where(VoltageReadingDB.timestamp >= cutoff_time)

        # Apply sensor filter
        if options.sensor_id:
            query = query.where(VoltageReadingDB.sensor_id == options.sensor_id)

        query = query.limit(options.limit)

        result = await db.execute(query)
        readings: List[VoltageReading] = []
        for row in result.scalars():
            readings.append(cast(VoltageReading, row))
        return readings

    @strawberry.field
    async def power_quality(
        self, info: Info[Any, Any], options: PowerQualityFilter
    ) -> List[PowerQuality]:
        """Get power quality data with optional filtering"""
        db: AsyncSession = info.context["db"]

        # Build query with time filtering
        query = select(PowerQualityDB).order_by(PowerQualityDB.timestamp.desc())

        # Apply time range filter
        if options.time_range:
            if (
                options.time_range.start_date is not None
                and options.time_range.end_date is not None
            ):
                query = query.where(
                    (PowerQualityDB.timestamp >= options.time_range.start_date)
                    & (PowerQualityDB.timestamp <= options.time_range.end_date)
                )
            else:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=options.time_range.hours)
                query = query.where(PowerQualityDB.timestamp >= cutoff_time)
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            query = query.where(PowerQualityDB.timestamp >= cutoff_time)

        # Apply sensor filter
        if options.sensor_id:
            query = query.where(PowerQualityDB.sensor_id == options.sensor_id)

        query = query.limit(options.limit)

        result = await db.execute(query)
        pqs: List[PowerQuality] = []
        for row in result.scalars():
            pqs.append(cast(PowerQuality, row))
        return pqs

    @strawberry.field
    async def fault_events(
        self, info: Info[Any, Any], options: FaultEventFilter
    ) -> List[FaultEvent]:
        """Get fault events with optional filtering by severity and time range"""
        db: AsyncSession = info.context["db"]

        query = select(FaultEventDB).order_by(FaultEventDB.timestamp.desc())

        # Apply time range filter
        if options.time_range:
            if (
                options.time_range.start_date is not None
                and options.time_range.end_date is not None
            ):
                query = query.where(
                    (FaultEventDB.timestamp >= options.time_range.start_date)
                    & (FaultEventDB.timestamp <= options.time_range.end_date)
                )
            else:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=options.time_range.hours)
                query = query.where(FaultEventDB.timestamp >= cutoff_time)
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            query = query.where(FaultEventDB.timestamp >= cutoff_time)

        # Apply severity filter
        if options.severity:
            query = query.where(FaultEventDB.severity == options.severity)

        query = query.limit(options.limit)

        result = await db.execute(query)
        faults: List[FaultEvent] = []
        for row in result.scalars():
            fault = FaultEvent(  # type: ignore[call-arg]
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

        # Get average power factor
        pf_query: Select[tuple[float | None]] = select(
            sa_func.avg(PowerQualityDB.power_factor).cast(Float)
        ).where(PowerQualityDB.timestamp >= fault_cutoff)
        pf_result = await db.execute(pf_query)
        avg_power_factor = float(pf_result.scalar() or 0.95)

        # Calculate offline sensors
        offline_sensors = total_sensors - active_sensors

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
            offline_sensors=offline_sensors,
            fault_count_24h=fault_count_24h,
            violation_count_24h=violation_count_24h,
            avg_voltage=avg_voltage,
            avg_power_factor=avg_power_factor,
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
            return MutationResult(  # type: ignore[call-arg]
                success=True, message="Voltage reading ingested", id=db_reading.id
            )
        except Exception as error:  # pylint: disable=broad-except
            await db.rollback()
            return MutationResult(  # type: ignore[call-arg]
                success=False, message=f"Error: {str(error)}"
            )

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
            return MutationResult(  # type: ignore[call-arg]
                success=True,
                message="Power quality data ingested",
                id=db_pq.id,
            )
        except Exception as error:  # pylint: disable=broad-except
            await db.rollback()
            return MutationResult(  # type: ignore[call-arg]
                success=False, message=f"Error: {str(error)}"
            )

    @strawberry.mutation
    async def create_fault_event(
        self, info: Info[Any, Any], event: FaultEventInput
    ) -> MutationResult:
        """Create a new fault event"""
        db: AsyncSession = info.context["db"]
        try:
            db_fault = FaultEventDB(
                sensor_id=event.event_id,  # Use event_id as sensor identifier
                severity=event.severity,
                fault_type=event.event_type,
                location=event.location,
                timestamp=event.timestamp,
                duration_ms=event.duration_ms,
                resolved=False,
                description=f"{event.event_type} fault at {event.location}",
            )
            db.add(db_fault)
            await db.commit()
            await db.refresh(db_fault)
            return MutationResult(  # type: ignore[call-arg]
                success=True, message="Fault event created", id=db_fault.id
            )
        except Exception as error:  # pylint: disable=broad-except
            await db.rollback()
            return MutationResult(  # type: ignore[call-arg]
                success=False, message=f"Error: {str(error)}"
            )


# ==============================================================================
# SUBSCRIPTIONS FOR REAL-TIME UPDATES
# ==============================================================================


@strawberry.type
class Subscription:
    """GraphQL Subscription root type for real-time updates"""

    @strawberry.subscription
    async def voltage_reading_updated(
        self, sensor_id: Optional[str] = None
    ) -> AsyncGenerator[VoltageReading, None]:
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
            yield VoltageReading(  # type: ignore[call-arg]
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
    ) -> AsyncGenerator[PowerQuality, None]:
        """Subscribe to power quality updates"""
        # Note: This requires WebSocket connection and event streaming infrastructure
        # Implementation requires message queue or event bus (Redis, RabbitMQ, etc.)
        try:
            # Placeholder: In production, subscribe to message queue
            yield PowerQuality(  # type: ignore[call-arg]
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
    ) -> AsyncGenerator[FaultEvent, None]:
        """Subscribe to fault event notifications"""
        # Note: This requires WebSocket connection and event streaming infrastructure
        # Implementation requires message queue or event bus (Redis, RabbitMQ, etc.)
        try:
            # Placeholder: In production, subscribe to message queue
            yield FaultEvent(  # type: ignore[call-arg]
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
