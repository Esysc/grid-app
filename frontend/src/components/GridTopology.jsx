import React, { useState } from 'react';
import './GridTopology.css';

const GridTopology = ({ sensorStatus = [], voltageData = [] }) => {
  const [selectedSensor, setSelectedSensor] = useState(null);

  // Map sensor locations to grid nodes with coordinates
  const nodes = [
    { id: 'main-hub', x: 250, y: 80, label: 'Main Hub', type: 'hub' },
    { id: 'substation-1', x: 80, y: 40, label: 'Substation A', type: 'substation', sensorType: 'voltage' },
    { id: 'substation-2', x: 420, y: 40, label: 'Substation B', type: 'substation', sensorType: 'voltage' },
    { id: 'transformer-1', x: 40, y: 200, label: 'Transformer 1', type: 'transformer' },
    { id: 'transformer-2', x: 460, y: 200, label: 'Transformer 2', type: 'transformer' },
    { id: 'feeder-1', x: 40, y: 300, label: 'Feeder 1', type: 'feeder' },
    { id: 'feeder-2', x: 250, y: 300, label: 'Feeder 3B', type: 'feeder', sensorType: 'voltage' },
    { id: 'feeder-3', x: 460, y: 300, label: 'Feeder 5A', type: 'feeder', sensorType: 'voltage' },
  ];

  const connections = [
    { from: 'substation-1', to: 'main-hub' },
    { from: 'substation-2', to: 'main-hub' },
    { from: 'main-hub', to: 'transformer-1' },
    { from: 'main-hub', to: 'transformer-2' },
    { from: 'transformer-1', to: 'feeder-1' },
    { from: 'transformer-1', to: 'feeder-2' },
    { from: 'transformer-2', to: 'feeder-2' },
    { from: 'transformer-2', to: 'feeder-3' },
  ];

  // Get sensor for a node
  const getSensorForNode = (nodeLabel) => {
    return sensorStatus.find((sensor) => sensor.location === nodeLabel);
  };

  // Get voltage value for sensor
  const getVoltageForSensor = (sensorId) => {
    const reading = voltageData.find((v) => v.sensor_id === sensorId);
    return reading ? (reading.voltage_l1 || 0).toFixed(1) : null;
  };

  // Determine node styling
  const getNodeColor = (node) => {
    const sensor = getSensorForNode(node.label);
    if (node.type === 'hub') return '#ff6b6b';
    if (node.type === 'transformer') return '#ffd700';
    if (sensor) {
      return sensor.is_operational ? '#4caf50' : '#ff5252';
    }
    return '#4fc3f7';
  };

  const getNodeBorder = (node) => {
    const sensor = getSensorForNode(node.label);
    if (sensor && !sensor.is_operational) return '#ff5252';
    return '#ffffff';
  };

  // SVG node component
  const SVGNode = ({ node }) => {
    const sensor = getSensorForNode(node.label);
    const voltage = sensor ? getVoltageForSensor(sensor.sensor_id) : null;
    const isFaulty = sensor && !sensor.is_operational;

    return (
      <g
        key={node.id}
        className={`svg-node ${isFaulty ? 'faulty-pulse' : ''}`}
        onClick={() => sensor && setSelectedSensor(sensor)}
        style={{ cursor: sensor ? 'pointer' : 'default' }}
      >
        {/* Connection lines will be drawn separately */}
        {/* Node circle */}
        <circle
          cx={node.x}
          cy={node.y}
          r={24}
          fill={getNodeColor(node)}
          stroke={getNodeBorder(node)}
          strokeWidth="2"
        />

        {/* Fault indicator ring */}
        {isFaulty && (
          <circle
            cx={node.x}
            cy={node.y}
            r={28}
            fill="none"
            stroke="#ff5252"
            strokeWidth="2"
            className="fault-ring"
          />
        )}

        {/* Node label */}
        <text
          x={node.x}
          y={node.y + 40}
          textAnchor="middle"
          className="node-label"
          fill="#ffffff"
        >
          {node.label}
        </text>

        {/* Sensor data if available */}
        {sensor && (
          <>
            <text
              x={node.x}
              y={node.y + 4}
              textAnchor="middle"
              className="sensor-value"
              fill="#ffffff"
              fontSize="11"
              fontWeight="bold"
            >
              {voltage ? `${voltage}V` : sensor.sensor_id}
            </text>
            <circle
              cx={node.x + 20}
              cy={node.y - 20}
              r="4"
              fill={sensor.is_operational ? '#4caf50' : '#ff5252'}
            />
          </>
        )}
      </g>
    );
  };

  // SVG connection component
  const SVGConnection = ({ from, to }) => {
    const fromNode = nodes.find((n) => n.id === from);
    const toNode = nodes.find((n) => n.id === to);

    if (!fromNode || !toNode) return null;

    return (
      <line
        key={`${from}-${to}`}
        x1={fromNode.x}
        y1={fromNode.y}
        x2={toNode.x}
        y2={toNode.y}
        stroke="#4fc3f7"
        strokeWidth="2"
        strokeOpacity="0.6"
      />
    );
  };

  return (
    <div className="grid-topology-container">
      <div className="grid-topology">
        <h2>🔌 Grid Topology & Sensor Network</h2>
        <svg
          width="100%"
          height="400"
          viewBox="0 0 520 340"
          className="topology-svg"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Draw connections first (background) */}
          {connections.map((conn) => (
            <SVGConnection key={`${conn.from}-${conn.to}`} from={conn.from} to={conn.to} />
          ))}

          {/* Draw nodes on top */}
          {nodes.map((node) => (
            <SVGNode key={node.id} node={node} />
          ))}
        </svg>

        <p className="topology-description">
          Interactive grid topology with real-time sensor data. Green = operational, Red = faulty.
          Click on sensor nodes for details.
        </p>
      </div>

      {/* Sensor list sidebar */}
      <div className="sensor-list-sidebar">
        <h3>📊 Active Sensors</h3>
        <div className="sensor-list">
          {sensorStatus.length === 0 ? (
            <p className="no-sensors">No sensors available</p>
          ) : (
            sensorStatus.map((sensor) => {
              const voltage = getVoltageForSensor(sensor.sensor_id);
              return (
                <div
                  key={sensor.sensor_id}
                  className={`sensor-item ${!sensor.is_operational ? 'faulty' : ''} ${
                    selectedSensor?.sensor_id === sensor.sensor_id ? 'selected' : ''
                  }`}
                  onClick={() => setSelectedSensor(sensor)}
                >
                  <div className="sensor-header">
                    <span className="sensor-status-dot" style={{
                      backgroundColor: sensor.is_operational ? '#4caf50' : '#ff5252',
                    }}></span>
                    <span className="sensor-id">{sensor.sensor_id}</span>
                  </div>
                  <div className="sensor-details">
                    <div className="sensor-location">{sensor.location}</div>
                    {voltage && (
                      <div className="sensor-reading">
                        <strong>V:</strong> {voltage}V
                      </div>
                    )}
                    <div className="sensor-time">
                      {sensor.seconds_since_update}s ago
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Sensor detail modal */}
      {selectedSensor && (
        <div className="modal-overlay" onClick={() => setSelectedSensor(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedSensor(null)}>✕</button>
            <h3>{selectedSensor.sensor_id}</h3>

            <div className="modal-grid">
              <div className="modal-section">
                <label>Location</label>
                <value>{selectedSensor.location}</value>
              </div>

              <div className="modal-section">
                <label>Type</label>
                <value>{selectedSensor.sensor_type}</value>
              </div>

              <div className="modal-section">
                <label>Status</label>
                <value className={selectedSensor.is_operational ? 'operational' : 'faulty'}>
                  {selectedSensor.is_operational ? '✅ Operational' : '❌ Faulty'}
                </value>
              </div>

              <div className="modal-section">
                <label>Last Update</label>
                <value>{selectedSensor.seconds_since_update}s ago</value>
              </div>

              {selectedSensor.sensor_type === 'voltage' && (
                <>
                  {(() => {
                    const reading = voltageData.find(
                      (v) => v.sensor_id === selectedSensor.sensor_id
                    );
                    return reading ? (
                      <>
                        <div className="modal-section">
                          <label>Voltage L1</label>
                          <value>{(reading.voltage_l1 || 0).toFixed(2)}V</value>
                        </div>
                        <div className="modal-section">
                          <label>Voltage L2</label>
                          <value>{(reading.voltage_l2 || 0).toFixed(2)}V</value>
                        </div>
                        <div className="modal-section">
                          <label>Voltage L3</label>
                          <value>{(reading.voltage_l3 || 0).toFixed(2)}V</value>
                        </div>
                        <div className="modal-section">
                          <label>Frequency</label>
                          <value>{(reading.frequency || 0).toFixed(2)}Hz</value>
                        </div>
                      </>
                    ) : null;
                  })()}
                </>
              )}
            </div>

            <button className="modal-close-btn" onClick={() => setSelectedSensor(null)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GridTopology;
