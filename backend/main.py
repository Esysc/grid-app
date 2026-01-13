"""
FastAPI Grid Monitoring Application with Auth and GraphQL
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from typing import cast as typing_cast

from auth import (
    ALGORITHM,
    SECRET_KEY,
    Token,
    User,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_user,
)
from data_generator import GridDataGenerator
from database import (
    FaultEventDB,
    PowerQualityDB,
    VoltageReadingDB,
    close_db,
    get_db,
    init_db,
)
from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from graphql_schema import schema
from jose import JWTError, jwt
from models import (
    FaultEvent,
    HealthCheck,
    PowerQualityMetrics,
    SensorStats,
    SensorStatus,
    VoltageReading,
)
from mqtt_consumer import start_mqtt_consumer, stop_mqtt_consumer
from s3_export import S3Exporter
from sqlalchemy import Float, and_
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from strawberry.fastapi import GraphQLRouter as _GraphQLRouter

HOURS_DESC = "Hours of historical data"

# Data generator instance
generator = GridDataGenerator()

# S3 exporter instance (will use LocalStack in Docker)
s3_exporter: S3Exporter = S3Exporter(
    endpoint_url="http://localstack:4566",
)


@asynccontextmanager
async def lifespan(
    app_instance: "FastAPI",  # pylint: disable=unused-argument
) -> AsyncIterator[None]:
    """Manage application lifespan events"""
    # Startup
    await init_db()
    print("✅ Database initialized")
    print("✅ GraphQL schema registered")
    print("✅ Authentication enabled")

    # Initialize S3 bucket with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            s3_exporter.ensure_bucket_exists()
            print("✅ S3 bucket initialized")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ S3 bucket initialization attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2)
            else:
                print(f"⚠️ S3 bucket initialization failed after {max_retries} attempts: {e}")

    # Start MQTT consumer in background
    mqtt_task = asyncio.create_task(start_mqtt_consumer())
    print("✅ MQTT consumer started")

    yield

    # Shutdown
    await stop_mqtt_consumer()
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass
    await close_db()
    print("👋 Application shutdown complete")
    print("✅ Database connections closed")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Grid Monitoring API",
    description=("Real-time grid monitoring and analytics platform with auth and GraphQL"),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GraphQL context function to provide database session
def get_context(db: AsyncSession = Depends(get_db)) -> Dict[str, AsyncSession]:
    """Provide database session to GraphQL resolvers"""
    return {"db": db}


# Mount GraphQL router with database context
graphql_app: _GraphQLRouter[Any, Any] = _GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/", tags=["Health"])
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "Grid Monitoring API",
        "version": "2.0.0",
        "docs": "/docs",
        "graphql": "/graphql",
    }


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Login endpoint to get JWT token"""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile"""
    return current_user


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        await db.execute(select(1))
        db_connected = True
    except Exception:
        db_connected = False

    return HealthCheck(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(timezone.utc),
        database_connected=db_connected,
    )


@app.get(
    "/sensors/voltage",
    response_model=List[VoltageReading],
    tags=["Sensors"],
)
async def get_voltage_readings(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    hours: int = Query(1, ge=1, le=168, description=HOURS_DESC),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[VoltageReading]:
    """Get voltage readings for the last N hours"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = select(VoltageReadingDB).where(VoltageReadingDB.timestamp >= cutoff_time)

    if sensor_id:
        query = query.where(VoltageReadingDB.sensor_id == sensor_id)

    query = query.order_by(VoltageReadingDB.timestamp.desc()).limit(1000)

    result = await db.execute(query)
    readings = result.scalars().all()

    return [VoltageReading.model_validate(r) for r in readings]


@app.post(
    "/sensors/voltage",
    response_model=VoltageReading,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensors", "Ingest"],
)
async def ingest_voltage(
    reading: VoltageReading,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> VoltageReading:
    """Ingest new voltage reading"""
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
    return VoltageReading.model_validate(db_reading)


@app.get(
    "/sensors/power-quality",
    response_model=List[PowerQualityMetrics],
    tags=["Sensors"],
)
async def get_power_quality(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    hours: int = Query(1, ge=1, le=168, description=HOURS_DESC),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[PowerQualityMetrics]:
    """Get power quality metrics for the last N hours"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = select(PowerQualityDB).where(PowerQualityDB.timestamp >= cutoff_time)

    if sensor_id:
        query = query.where(PowerQualityDB.sensor_id == sensor_id)

    query = query.order_by(PowerQualityDB.timestamp.desc()).limit(1000)

    result = await db.execute(query)
    metrics = result.scalars().all()

    return [PowerQualityMetrics.model_validate(m) for m in metrics]


@app.post(
    "/sensors/power-quality",
    response_model=PowerQualityMetrics,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensors", "Ingest"],
)
async def ingest_power_quality(
    metrics: PowerQualityMetrics,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PowerQualityMetrics:
    """Ingest new power quality metrics"""
    db_metrics = PowerQualityDB(
        timestamp=metrics.timestamp,
        sensor_id=metrics.sensor_id,
        location=metrics.location,
        thd_voltage=metrics.thd_voltage,
        thd_current=metrics.thd_current,
        power_factor=metrics.power_factor,
        voltage_imbalance=metrics.voltage_imbalance,
        flicker_severity=metrics.flicker_severity,
    )
    db.add(db_metrics)
    await db.commit()
    await db.refresh(db_metrics)
    return PowerQualityMetrics.model_validate(db_metrics)


@app.get(
    "/sensors/list",
    response_model=List[str],
    tags=["Sensors"],
)
async def list_active_sensors(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[str]:
    """Get list of all active sensors (from last 1 hour)"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

    # Get unique sensor IDs from voltage readings
    voltage_query: Select[Tuple[str]] = (
        select(VoltageReadingDB.sensor_id)
        .where(VoltageReadingDB.timestamp >= cutoff_time)
        .distinct()
    )
    voltage_result = await db.execute(voltage_query)
    voltage_sensors = [row[0] for row in voltage_result.fetchall()]

    # Get unique sensor IDs from power quality
    pq_query: Select[Tuple[str]] = (
        select(PowerQualityDB.sensor_id).where(PowerQualityDB.timestamp >= cutoff_time).distinct()
    )
    pq_result = await db.execute(pq_query)
    pq_sensors = [row[0] for row in pq_result.fetchall()]

    # Combine and deduplicate
    all_sensors = list(set(voltage_sensors + pq_sensors))
    return sorted(all_sensors)


@app.get(
    "/sensors/status",
    response_model=List[SensorStatus],
    tags=["Sensors"],
)
async def get_sensor_status(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[SensorStatus]:
    """Get current status of all active sensors with latest readings"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
    now = datetime.now(timezone.utc)
    sensor_statuses: List[SensorStatus] = []

    # Get latest voltage readings for each sensor
    voltage_query = (
        select(VoltageReadingDB)
        .where(VoltageReadingDB.timestamp >= cutoff_time)
        .order_by(VoltageReadingDB.sensor_id, VoltageReadingDB.timestamp.desc())
    )
    voltage_result = await db.execute(voltage_query)
    voltage_readings = voltage_result.scalars().all()

    # Track which sensors we've already processed
    processed_sensors: set[str] = set()

    for reading in voltage_readings:
        if reading.sensor_id not in processed_sensors:
            seconds_since = int((now - reading.timestamp).total_seconds())
            sensor_status_obj = SensorStatus(
                sensor_id=reading.sensor_id,
                sensor_type="voltage",
                location=reading.location,
                last_reading_timestamp=reading.timestamp,
                is_operational=seconds_since < 60,  # Operational if data < 1 min old
                seconds_since_update=seconds_since,
                latest_value=reading.voltage_l1,
            )
            sensor_statuses.append(sensor_status_obj)
            processed_sensors.add(reading.sensor_id)

    # Get latest power quality readings for each sensor
    pq_query = (
        select(PowerQualityDB)
        .where(PowerQualityDB.timestamp >= cutoff_time)
        .order_by(PowerQualityDB.sensor_id, PowerQualityDB.timestamp.desc())
    )
    pq_result = await db.execute(pq_query)
    pq_readings = pq_result.scalars().all()

    for reading in pq_readings:
        if reading.sensor_id not in processed_sensors:
            seconds_since = int((now - reading.timestamp).total_seconds())
            sensor_status_pq = SensorStatus(
                sensor_id=reading.sensor_id,
                sensor_type="power_quality",
                location=reading.location,
                last_reading_timestamp=reading.timestamp,
                is_operational=seconds_since < 60,
                seconds_since_update=seconds_since,
                latest_value=reading.power_factor,
            )
            sensor_statuses.append(sensor_status_pq)
            processed_sensors.add(reading.sensor_id)

    return sorted(sensor_statuses, key=lambda x: x.sensor_id)


@app.get(
    "/faults/recent",
    response_model=List[FaultEvent],
    tags=["Faults"],
)
async def get_recent_faults(
    hours: int = Query(24, ge=1, le=168, description=HOURS_DESC),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[FaultEvent]:
    """Get fault events from the last N hours"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = select(FaultEventDB).where(FaultEventDB.timestamp >= cutoff_time)

    if severity:
        query = query.where(FaultEventDB.severity == severity)

    query = query.order_by(FaultEventDB.timestamp.desc()).limit(500)

    result = await db.execute(query)
    faults = result.scalars().all()

    return [FaultEvent.model_validate(f) for f in faults]


@app.post(
    "/faults",
    response_model=FaultEvent,
    status_code=status.HTTP_201_CREATED,
    tags=["Faults", "Ingest"],
)
async def ingest_fault_event(
    fault: FaultEvent,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FaultEvent:
    """Ingest new fault event"""
    db_fault = FaultEventDB(
        timestamp=fault.timestamp,
        sensor_id=fault.sensor_id,
        location=fault.location,
        fault_type=fault.fault_type,
        severity=fault.severity,
        voltage_drop=fault.voltage_drop,
        duration_ms=fault.duration_ms,
        resolved=fault.resolved,
        description=fault.description,
    )
    db.add(db_fault)
    await db.commit()
    await db.refresh(db_fault)
    return FaultEvent.model_validate(db_fault)


@app.get(
    "/faults/timeline",
    response_model=List[FaultEvent],
    tags=["Faults"],
)
async def get_fault_timeline(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[FaultEvent]:
    """Get fault timeline for date range"""
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    query = (
        select(FaultEventDB)
        .where(
            and_(
                FaultEventDB.timestamp >= start_date,
                FaultEventDB.timestamp <= end_date,
            )
        )
        .order_by(FaultEventDB.timestamp.desc())
    )

    result = await db.execute(query)
    faults = result.scalars().all()

    return [FaultEvent.model_validate(f) for f in faults]


@app.get("/stats", response_model=SensorStats, tags=["Analytics"])
async def get_sensor_stats(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SensorStats:
    """Get aggregated sensor statistics"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

    # Count sensors (simplified - in production, track sensor status)
    total_sensors = 4
    active_sensors = 4
    offline_sensors = 0

    # Average voltage
    voltage_query: Select[Tuple[Optional[float]]] = select(
        typing_cast(Any, sa_func.avg(VoltageReadingDB.voltage_l1).cast(Float))
    ).where(VoltageReadingDB.timestamp >= cutoff_time)
    voltage_result = await db.execute(voltage_query)
    avg_voltage = voltage_result.scalar() or 230.0

    # Average power factor
    pf_query: Select[Tuple[Optional[float]]] = select(
        typing_cast(Any, sa_func.avg(PowerQualityDB.power_factor))
    ).where(PowerQualityDB.timestamp >= cutoff_time)
    pf_result = await db.execute(pf_query)
    avg_power_factor = pf_result.scalar() or 0.95

    # Total faults in last 24h
    # pylint: disable=not-callable
    fault_query: Select[Tuple[int]] = select(
        typing_cast(Any, sa_func.count(FaultEventDB.id))
    ).where(FaultEventDB.timestamp >= cutoff_time)
    fault_result = await db.execute(fault_query)
    total_faults_24h = fault_result.scalar() or 0

    # Count voltage violations (last 24h) - voltage outside 207-253V range
    violation_query: Select[Tuple[int]] = select(
        typing_cast(Any, sa_func.count(VoltageReadingDB.id))
    ).where(
        VoltageReadingDB.timestamp >= cutoff_time,
        (VoltageReadingDB.voltage_l1 < 207.0) | (VoltageReadingDB.voltage_l1 > 253.0),
    )
    violation_result = await db.execute(violation_query)
    quality_violations = violation_result.scalar() or 0

    return SensorStats(
        total_sensors=total_sensors,
        active_sensors=active_sensors,
        offline_sensors=offline_sensors,
        avg_voltage=round(avg_voltage, 2),
        avg_power_factor=round(avg_power_factor, 3),
        total_faults_24h=total_faults_24h,
        quality_violations=quality_violations,
    )


@app.get("/stream/updates", tags=["Real-time"])
async def stream_updates(
    token: str = Query(..., description="JWT token for authentication"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE endpoint for real-time updates (token via query string).

    Token authentication passed as query parameter for EventSource compatibility.
    """
    # Validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    # Touch dependency to satisfy linting
    _ = db

    async def event_generator():
        """Generate SSE events with live sensor data"""
        try:
            while True:
                # Generate live data
                voltage = generator.generate_voltage_reading()
                power_quality = generator.generate_power_quality()

                # Occasionally generate fault events (5% chance)
                fault = None
                if asyncio.get_event_loop().time() % 20 < 1:  # Roughly every 20 seconds
                    fault = generator.generate_fault_event()

                # Build event data
                event_data: Dict[str, Any] = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "voltage": voltage.model_dump(mode="json"),
                    "power_quality": power_quality.model_dump(mode="json"),
                }

                if fault:
                    event_data["fault"] = fault.model_dump(mode="json")

                # Send SSE event
                yield f"data: {json.dumps(event_data)}\n\n"

                await asyncio.sleep(2)  # Update every 2 seconds

        except asyncio.CancelledError:
            print("SSE connection closed")
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/export/voltage", tags=["Export"])
async def export_voltage_data(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Export voltage data to S3"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(VoltageReadingDB)
        .where(VoltageReadingDB.timestamp >= cutoff_time)
        .order_by(VoltageReadingDB.timestamp.desc())
    )

    result = await db.execute(query)
    readings = result.scalars().all()

    data = [r.__dict__ for r in readings]
    return s3_exporter.export_voltage_data(data, hours=hours)


@app.post("/export/faults", tags=["Export"])
async def export_fault_data(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Export fault events to S3"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(FaultEventDB)
        .where(FaultEventDB.timestamp >= cutoff_time)
        .order_by(FaultEventDB.timestamp.desc())
    )

    result = await db.execute(query)
    faults = result.scalars().all()

    data = [f.__dict__ for f in faults]
    return s3_exporter.export_fault_events(data)


@app.get("/export/list", tags=["Export"])
async def list_exports(
    _current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """List all exported files"""
    return s3_exporter.list_exports()


@app.get("/export/{file_key:path}", tags=["Export"])
async def get_export_url(
    file_key: str = Path(..., description="Key of the export file in S3"),
    expires_in: int = Query(3600, ge=60, le=86400, description="Presigned URL lifetime (seconds)"),
    _current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate a presigned URL to download an export file"""
    return s3_exporter.generate_presigned_url(key=file_key, expires_in=expires_in)


@app.post("/simulate/populate", tags=["Development"])
async def populate_test_data(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to generate"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Populate database with test data (development only)"""
    (
        voltage_readings,
        power_quality,
        fault_events,
    ) = generator.generate_historical_data(hours=hours)

    # Insert voltage readings
    for reading in voltage_readings:
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

    # Insert power quality metrics
    for pq in power_quality:
        db_pq = PowerQualityDB(
            timestamp=pq.timestamp,
            sensor_id=pq.sensor_id,
            location=pq.location,
            thd_voltage=pq.thd_voltage,
            thd_current=pq.thd_current,
            power_factor=pq.power_factor,
            voltage_imbalance=pq.voltage_imbalance,
            flicker_severity=pq.flicker_severity,
        )
        db.add(db_pq)

    # Insert fault events
    for fault in fault_events:
        db_fault = FaultEventDB(
            timestamp=fault.timestamp,
            sensor_id=fault.sensor_id,
            location=fault.location,
            fault_type=fault.fault_type,
            severity=fault.severity,
            voltage_drop=fault.voltage_drop,
            duration_ms=fault.duration_ms,
            resolved=fault.resolved,
            description=fault.description,
        )
        db.add(db_fault)

    await db.commit()

    return {
        "message": "Test data populated successfully",
        "voltage_readings": len(voltage_readings),
        "power_quality_metrics": len(power_quality),
        "fault_events": len(fault_events),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
