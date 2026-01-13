"""
MQTT Sensor Simulator - Simulates real grid sensors with different operational states

This simulator runs independently and publishes sensor data to MQTT topics.
It can simulate:
- Operational (normal) state with realistic variations
- Faulty state with anomalies and errors
- Recovery/Resume state transitioning from faulty to operational
"""

import asyncio
import json
import os
import random
from enum import Enum
from typing import Any, Dict

import aiomqtt  # pylint: disable=import-error
from data_generator import GridDataGenerator


class SensorState(Enum):
    """Operational states for simulated sensors"""

    OPERATIONAL = "operational"
    FAULTY = "faulty"
    RECOVERING = "recovering"


class VirtualSensor:
    """Represents a single virtual sensor with state management"""

    def __init__(self, sensor_id: str, location: str, sensor_type: str):
        self.sensor_id = sensor_id
        self.location = location
        self.sensor_type = sensor_type  # 'voltage' or 'power_quality'
        self.state = SensorState.OPERATIONAL
        self.fault_counter = 0
        self.recovery_counter = 0
        self.generator = GridDataGenerator()

    async def transition_state(self) -> None:
        """Randomly transition between states"""
        if self.state == SensorState.OPERATIONAL:
            # 5% chance to go faulty
            if random.random() < 0.05:
                self.state = SensorState.FAULTY
                self.fault_counter = random.randint(3, 10)  # Faulty for 3-10 readings
                print(f"🔴 {self.sensor_id} entering FAULTY state")

        elif self.state == SensorState.FAULTY:
            self.fault_counter -= 1
            if self.fault_counter <= 0:
                self.state = SensorState.RECOVERING
                self.recovery_counter = random.randint(2, 5)  # Recovery takes 2-5 readings
                print(f"🟡 {self.sensor_id} entering RECOVERING state")

        elif self.state == SensorState.RECOVERING:
            self.recovery_counter -= 1
            if self.recovery_counter <= 0:
                self.state = SensorState.OPERATIONAL
                print(f"🟢 {self.sensor_id} returned to OPERATIONAL state")

    def generate_reading(self) -> Dict[str, Any]:
        """Generate sensor reading based on current state."""
        if self.sensor_type == "voltage":
            reading = self.generator.generate_voltage_reading(
                sensor_id=self.sensor_id, location=self.location
            )
            voltage_data: Dict[str, Any] = {
                "sensor_id": reading.sensor_id,
                "location": reading.location,
                "timestamp": reading.timestamp.isoformat(),
                "voltage_l1": reading.voltage_l1,
                "voltage_l2": reading.voltage_l2,
                "voltage_l3": reading.voltage_l3,
                "frequency": reading.frequency,
            }

            # Modify based on state
            if self.state == SensorState.FAULTY:
                # Inject severe anomalies
                voltage_data["voltage_l1"] *= random.uniform(0.7, 1.4)  # ±30% variation
                voltage_data["voltage_l2"] *= random.uniform(0.7, 1.4)
                voltage_data["voltage_l3"] *= random.uniform(0.7, 1.4)
                voltage_data["frequency"] += random.uniform(-2, 2)  # Large frequency deviation
                voltage_data["state"] = "faulty"

            elif self.state == SensorState.RECOVERING:
                # Moderate anomalies, improving
                voltage_data["voltage_l1"] *= random.uniform(0.9, 1.1)  # ±10% variation
                voltage_data["voltage_l2"] *= random.uniform(0.9, 1.1)
                voltage_data["voltage_l3"] *= random.uniform(0.9, 1.1)
                voltage_data["frequency"] += random.uniform(-0.5, 0.5)
                voltage_data["state"] = "recovering"
            else:
                voltage_data["state"] = "operational"

            return voltage_data

        # power_quality sensor type
        pq_reading = self.generator.generate_power_quality(
            sensor_id=self.sensor_id, location=self.location
        )
        pq_data: Dict[str, Any] = {
            "sensor_id": pq_reading.sensor_id,
            "location": pq_reading.location,
            "timestamp": pq_reading.timestamp.isoformat(),
            "thd_voltage": pq_reading.thd_voltage,
            "thd_current": pq_reading.thd_current,
            "power_factor": pq_reading.power_factor,
            "voltage_imbalance": pq_reading.voltage_imbalance,
            "flicker_severity": pq_reading.flicker_severity,
        }

        # Modify based on state
        if self.state == SensorState.FAULTY:
            # Severe power quality issues
            pq_data["thd_voltage"] *= random.uniform(2.0, 3.0)
            pq_data["thd_current"] *= random.uniform(2.0, 3.0)
            pq_data["power_factor"] *= random.uniform(0.7, 0.85)
            pq_data["voltage_imbalance"] *= random.uniform(3.0, 5.0)
            pq_data["flicker_severity"] *= random.uniform(2.0, 4.0)
            pq_data["state"] = "faulty"

        elif self.state == SensorState.RECOVERING:
            # Moderate issues, improving
            pq_data["thd_voltage"] *= random.uniform(1.2, 1.5)
            pq_data["thd_current"] *= random.uniform(1.2, 1.5)
            pq_data["power_factor"] *= random.uniform(0.85, 0.92)
            pq_data["voltage_imbalance"] *= random.uniform(1.5, 2.5)
            pq_data["flicker_severity"] *= random.uniform(1.2, 2.0)
            pq_data["state"] = "recovering"
        else:
            pq_data["state"] = "operational"

        return pq_data


class SensorSimulator:
    """Main simulator that manages multiple virtual sensors"""

    def __init__(self, mqtt_broker: str = "mqtt://localhost:1883"):
        self.mqtt_broker = mqtt_broker
        self.sensors: list[VirtualSensor] = []
        self.running = False

    def create_sensors(self) -> None:
        """Create virtual sensors matching the grid topology"""
        sensor_configs = [
            # Voltage sensors
            ("VS-001", "Substation A", "voltage"),
            ("VS-002", "Substation B", "voltage"),
            ("VS-003", "Feeder 3B", "voltage"),
            ("VS-004", "Feeder 5A", "voltage"),
            # Power quality sensors
            ("PQ-001", "Substation A", "power_quality"),
            ("PQ-002", "Substation B", "power_quality"),
            ("PQ-003", "Feeder 3B", "power_quality"),
            ("PQ-004", "Feeder 5A", "power_quality"),
        ]

        for sensor_id, location, sensor_type in sensor_configs:
            self.sensors.append(VirtualSensor(sensor_id, location, sensor_type))

        print(f"✅ Created {len(self.sensors)} virtual sensors")

    async def publish_sensor_data(self, client: aiomqtt.Client) -> None:
        """Continuously publish sensor data"""
        while self.running:
            for sensor in self.sensors:
                # Transition state
                await sensor.transition_state()

                # Generate and publish reading
                reading = sensor.generate_reading()
                topic = f"grid/sensors/{sensor.sensor_type}/{sensor.sensor_id}"

                await client.publish(topic, payload=json.dumps(reading), qos=1)

                # Log based on state
                state_emoji = {"operational": "✅", "faulty": "❌", "recovering": "⚠️"}
                emoji = state_emoji.get(reading["state"], "ℹ️")
                print(f"{emoji} {sensor.sensor_id} [{reading['state']}] -> {topic}")

            # Publish at intervals (every 5 seconds)
            await asyncio.sleep(5)

    async def run(self) -> None:
        """Main run loop"""
        self.create_sensors()
        self.running = True

        print(f"🚀 Starting sensor simulator, connecting to {self.mqtt_broker}")

        # Parse MQTT broker URL
        broker_url = self.mqtt_broker.replace("mqtt://", "")

        # Split hostname and port
        if ":" in broker_url:
            hostname, port_str = broker_url.split(":", 1)
            port_num: int = int(port_str)
        else:
            hostname = broker_url
            port_num = 1883  # Default MQTT port

        # Retry connection with exponential backoff
        retry_delay = 2
        max_retry_delay = 30

        while self.running:
            try:
                print(f"🔍 Attempting connection to: {hostname}:{port_num}")
                async with aiomqtt.Client(hostname=hostname, port=port_num) as client:
                    print("✅ Connected to MQTT broker")
                    retry_delay = 2  # Reset retry delay on successful connection
                    await self.publish_sensor_data(client)
            except KeyboardInterrupt:
                print("\n⏹️  Sensor simulator stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                if self.running:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)

        self.running = False


async def main() -> None:
    """Entry point for the sensor simulator"""
    mqtt_broker = os.getenv("MQTT_BROKER", "mqtt://localhost:1883")

    print("=" * 60)
    print("Grid Sensor Simulator - MQTT Edition")
    print("=" * 60)
    print(f"MQTT Broker: {mqtt_broker}")
    print("Publishing interval: 5 seconds")
    print("States: OPERATIONAL → FAULTY → RECOVERING → OPERATIONAL")
    print("=" * 60)
    print()

    simulator = SensorSimulator(mqtt_broker)
    await simulator.run()


if __name__ == "__main__":
    asyncio.run(main())
