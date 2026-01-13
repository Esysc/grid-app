#!/bin/bash

# Quick test script for MQTT sensor simulator
# This runs the simulator locally and shows real-time MQTT messages

echo "╔════════════════════════════════════════════════════╗"
echo "║   Grid Sensor Simulator - Local Test              ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Check if MQTT broker is running
if ! docker ps | grep -q grid-mqtt; then
    echo "❌ MQTT broker not running. Starting services..."
    docker-compose up -d mqtt
    sleep 3
fi

echo "✅ MQTT broker is running"
echo ""
echo "🎧 Subscribing to all sensor topics..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Subscribe to all topics and display them
docker exec -it grid-mqtt mosquitto_sub -t "grid/sensors/#" -v -F "@Y-@m-@dT@H:@M:@S %t %p"
