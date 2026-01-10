"""
Database connection and schema for TimescaleDB
"""

import os
from datetime import datetime
from typing import AsyncGenerator

from dotenv import load_dotenv  # pylint: disable=import-error
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Load environment variables from .env file
load_dotenv()

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://grid_user:your_password_here@localhost:5432/grid_monitoring",
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True, pool_size=5, max_overflow=10)

# Session factory
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# SQLAlchemy ORM Models
class VoltageReadingDB(Base):
    __tablename__ = "voltage_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sensor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    voltage_l1: Mapped[float] = mapped_column(Float, nullable=False)
    voltage_l2: Mapped[float] = mapped_column(Float, nullable=False)
    voltage_l3: Mapped[float] = mapped_column(Float, nullable=False)
    frequency: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (Index("idx_voltage_sensor_time", "sensor_id", "timestamp"),)


class PowerQualityDB(Base):
    __tablename__ = "power_quality"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sensor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    thd_voltage: Mapped[float] = mapped_column(Float, nullable=False)
    thd_current: Mapped[float] = mapped_column(Float, nullable=False)
    power_factor: Mapped[float] = mapped_column(Float, nullable=False)
    voltage_imbalance: Mapped[float] = mapped_column(Float, nullable=False)
    flicker_severity: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (Index("idx_pq_sensor_time", "sensor_id", "timestamp"),)


class FaultEventDB(Base):
    __tablename__ = "fault_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sensor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    fault_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    voltage_drop: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_fault_time", "timestamp"),
        Index("idx_fault_severity", "severity"),
    )


# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for FastAPI dependency injection"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database schema"""
    # Create tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Try to convert to TimescaleDB hypertables in a separate transaction
    # This allows tables to exist even if hypertable conversion fails
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "SELECT create_hypertable('voltage_readings', "
                    "'timestamp', if_not_exists => TRUE);"
                )
            )
            await conn.execute(
                text(
                    "SELECT create_hypertable('power_quality', "
                    "'timestamp', if_not_exists => TRUE);"
                )
            )
            await conn.execute(
                text(
                    "SELECT create_hypertable('fault_events', "
                    "'timestamp', if_not_exists => TRUE);"
                )
            )
    except Exception as e:
        print(
            f"Note: TimescaleDB hypertables not created " f"(extension may not be installed): {e}"
        )


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
