"""
MQTT Consumer for Grid Monitoring - Listens to sensor data and stores it in the database

This consumer runs as a background task in the FastAPI application and listens
to MQTT topics where sensors publish their data.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import aiomqtt
from database import get_db
from models import PowerQualityMetrics, VoltageReading
from sqlalchemy.ext.asyncio import AsyncSession


class MQTTConsumer:
    """MQTT consumer that listens for sensor data and stores it in the database"""

    def __init__(self, mqtt_broker: str = "mqtt://localhost:1883"):
        self.mqtt_broker = mqtt_broker
        self.running = False

    async def process_voltage_reading(self, data: Dict[str, Any], session: AsyncSession) -> None:
        """Process and store voltage reading"""
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(data["timestamp"])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Create VoltageReading instance
            reading = VoltageReading(
                sensor_id=data["sensor_id"],
                location=data["location"],
                timestamp=timestamp,
                voltage_l1=float(data["voltage_l1"]),
                voltage_l2=float(data["voltage_l2"]),
                voltage_l3=float(data["voltage_l3"]),
                frequency=float(data["frequency"]),
            )

            # Store in database
            from database import VoltageReadingDB

            db_reading = VoltageReadingDB(
                sensor_id=reading.sensor_id,
                location=reading.location,
                timestamp=reading.timestamp,
                voltage_l1=reading.voltage_l1,
                voltage_l2=reading.voltage_l2,
                voltage_l3=reading.voltage_l3,
                frequency=reading.frequency,
            )
            session.add(db_reading)
            await session.commit()

            state = data.get("state", "unknown")
            print(
                f"📊 Stored voltage reading: {reading.sensor_id} [{state}] "
                f"V_L1={reading.voltage_l1:.2f}V"
            )

        except Exception as e:
            print(f"❌ Error processing voltage reading: {e}")
            await session.rollback()

    async def process_power_quality(self, data: Dict[str, Any], session: AsyncSession) -> None:
        """Process and store power quality metrics"""
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(data["timestamp"])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Create PowerQualityMetrics instance
            metrics = PowerQualityMetrics(
                sensor_id=data["sensor_id"],
                location=data["location"],
                timestamp=timestamp,
                thd_voltage=float(data["thd_voltage"]),
                thd_current=float(data["thd_current"]),
                power_factor=float(data["power_factor"]),
                voltage_imbalance=float(data["voltage_imbalance"]),
                flicker_severity=float(data["flicker_severity"]),
            )

            # Store in database
            from database import PowerQualityDB

            db_metrics = PowerQualityDB(
                sensor_id=metrics.sensor_id,
                location=metrics.location,
                timestamp=metrics.timestamp,
                thd_voltage=metrics.thd_voltage,
                thd_current=metrics.thd_current,
                power_factor=metrics.power_factor,
                voltage_imbalance=metrics.voltage_imbalance,
                flicker_severity=metrics.flicker_severity,
            )
            session.add(db_metrics)
            await session.commit()

            state = data.get("state", "unknown")
            print(
                f"📈 Stored power quality: {metrics.sensor_id} [{state}] "
                f"THD_V={metrics.thd_voltage:.2f}%"
            )

        except Exception as e:
            print(f"❌ Error processing power quality: {e}")
            await session.rollback()

    async def consume_messages(self) -> None:
        """Main consumer loop - listen to MQTT topics and process messages"""
        broker_url = self.mqtt_broker.replace("mqtt://", "")

        # Split hostname and port
        if ":" in broker_url:
            hostname, port = broker_url.split(":", 1)
            port = int(port)
        else:
            hostname = broker_url
            port = 1883  # Default MQTT port

        print(f"🎧 MQTT Consumer starting, connecting to {hostname}:{port}")

        try:
            async with aiomqtt.Client(hostname=hostname, port=port) as client:
                # Subscribe to all sensor topics
                await client.subscribe("grid/sensors/#")
                print("✅ Subscribed to grid/sensors/#")

                async for message in client.messages:
                    if not self.running:
                        break

                    try:
                        # Parse message
                        payload = message.payload
                        if isinstance(payload, bytes):
                            payload = payload.decode()
                        elif not isinstance(payload, str):
                            payload = str(payload)
                        data = json.loads(payload)
                        topic = str(message.topic)

                        # Get database session
                        async for session in get_db():
                            # Route based on sensor type
                            if "/voltage/" in topic:
                                await self.process_voltage_reading(data, session)
                            elif "/power_quality/" in topic:
                                await self.process_power_quality(data, session)
                            else:
                                print(f"⚠️ Unknown topic: {topic}")
                            break  # Exit the session generator

                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON: {e}")
                    except Exception as e:
                        print(f"❌ Error processing message: {e}")

        except Exception as e:
            print(f"❌ MQTT Consumer error: {e}")
            # Retry after delay
            await asyncio.sleep(5)
            if self.running:
                print("🔄 Retrying MQTT connection...")
                await self.consume_messages()

    async def start(self) -> None:
        """Start the consumer"""
        self.running = True
        await self.consume_messages()

    async def stop(self) -> None:
        """Stop the consumer"""
        self.running = False
        print("⏹️ MQTT Consumer stopped")


# Global consumer instance
mqtt_consumer: MQTTConsumer | None = None


async def start_mqtt_consumer() -> None:
    """Start the MQTT consumer as a background task"""
    global mqtt_consumer

    mqtt_broker = os.getenv("MQTT_BROKER", "mqtt://mqtt:1883")
    mqtt_consumer = MQTTConsumer(mqtt_broker)

    print("🚀 Starting MQTT consumer...")
    await mqtt_consumer.start()


async def stop_mqtt_consumer() -> None:
    """Stop the MQTT consumer"""
    global mqtt_consumer

    if mqtt_consumer:
        await mqtt_consumer.stop()
