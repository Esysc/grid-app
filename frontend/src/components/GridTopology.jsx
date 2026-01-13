import React, { useMemo, useState } from 'react';
import './GridTopology.css';

const GridTopology = ({ sensorStatus = [], voltageData = [] }) => {
  const [selectedSensor, setSelectedSensor] = useState(null);

  // Known layout coordinates for key locations
  const baseLayout = {
    'Main Hub': { id: 'main-hub', x: 250, y: 80, label: 'Main Hub', type: 'hub' },
    'Substation A': { id: 'substation-1', x: 80, y: 40, label: 'Substation A', type: 'substation', sensorType: 'voltage' },
    'Substation B': { id: 'substation-2', x: 420, y: 40, label: 'Substation B', type: 'substation', sensorType: 'voltage' },
    'Transformer 1': { id: 'transformer-1', x: 40, y: 200, label: 'Transformer 1', type: 'transformer', sensorType: 'power_quality' },
    'Transformer 2': { id: 'transformer-2', x: 460, y: 200, label: 'Transformer 2', type: 'transformer', sensorType: 'power_quality' },
    'Feeder 1': { id: 'feeder-1', x: 40, y: 300, label: 'Feeder 1', type: 'feeder', sensorType: 'power_quality' },
    'Feeder 3B': { id: 'feeder-2', x: 250, y: 300, label: 'Feeder 3B', type: 'feeder', sensorType: 'voltage' },
    'Feeder 5A': { id: 'feeder-3', x: 460, y: 300, label: 'Feeder 5A', type: 'feeder', sensorType: 'voltage' },
  };

  const baseConnections = [
    { from: 'substation-1', to: 'main-hub' },
    { from: 'substation-2', to: 'main-hub' },
    { from: 'main-hub', to: 'transformer-1' },
    { from: 'main-hub', to: 'transformer-2' },
    { from: 'transformer-1', to: 'feeder-1' },
    { from: 'transformer-1', to: 'feeder-2' },
    { from: 'transformer-2', to: 'feeder-2' },
    { from: 'transformer-2', to: 'feeder-3' },
  ];

  // Build nodes: always show base layout, then add any unknown sensor locations
  const nodes = useMemo(() => {
    // Start with all base layout nodes (grid infrastructure)
    const dynamicNodes = Object.values(baseLayout).map(node => ({ ...node }));
    
    // Update sensor types based on actual sensors present
    const uniqueLocations = Array.from(new Set(sensorStatus.map((s) => s.location)));
    const unknownLocations = [];
    
    uniqueLocations.forEach((location) => {
      const sensorsHere = sensorStatus.filter((s) => s.location === location);
      const hasVoltage = sensorsHere.some((s) => s.sensor_id.startsWith('VS-'));
      const hasPQ = sensorsHere.some((s) => s.sensor_id.startsWith('PQ-'));
      const preferredType = hasVoltage ? 'voltage' : hasPQ ? 'power_quality' : undefined;
      
      const knownNode = dynamicNodes.find(n => n.label === location);
      if (knownNode) {
        knownNode.sensorType = preferredType || knownNode.sensorType;
      } else {
        unknownLocations.push({ location, preferredType });
      }
    });

    // Auto-place unknown locations in a ring around the hub
    const centerX = 250;
    const centerY = 180;
    const radius = 160;
    unknownLocations.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / Math.max(unknownLocations.length, 1);
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      dynamicNodes.push({
        id: `auto-${index}`,
        x,
        y,
        label: node.location,
        type: 'feeder',
        sensorType: node.preferredType,
      });
    });

    return dynamicNodes;
  }, [sensorStatus]);

  // Connections include base ones that exist plus default hub links for auto nodes
  const connections = useMemo(() => {
    const nodeIds = new Set(nodes.map((n) => n.id));
    const filteredBase = baseConnections.filter((c) => nodeIds.has(c.from) && nodeIds.has(c.to));

    const autoLinks = nodes
      .filter((n) => n.id.startsWith('auto-'))
      .map((n) => ({ from: n.id, to: 'main-hub' }));

    return [...filteredBase, ...autoLinks];
  }, [nodes]);

  // Get sensors for a node (all sensors at the location)
  const getSensorsForNode = (nodeLabel) => {
    return sensorStatus.filter((sensor) => sensor.location === nodeLabel);
  };

  // Get voltage value for sensor
  const getVoltageForSensor = (sensorId) => {
    const reading = voltageData.find((v) => v.sensor_id === sensorId);
    return reading ? (reading.voltage_l1 || 0).toFixed(1) : null;
  };

  // Determine node styling
  const getNodeColor = (node) => {
    const sensors = getSensorsForNode(node.label);
    if (node.type === 'hub') return '#ff6b6b';
    if (node.type === 'transformer') return '#ffd700';
    if (sensors.length > 0) {
      const anyFault = sensors.some((s) => !s.is_operational);
      return anyFault ? '#ff5252' : '#4caf50';
    }
    return '#4fc3f7';
  };

  const getNodeBorder = (node) => {
    const sensors = getSensorsForNode(node.label);
    if (sensors.some((s) => !s.is_operational)) return '#ff5252';
    return '#ffffff';
  };

  // SVG node component
  const SVGNode = ({ node }) => {
    const sensors = getSensorsForNode(node.label);
    const isFaulty = sensors.some((s) => !s.is_operational);

    return (
      <g
        key={node.id}
        className={`svg-node ${isFaulty ? 'faulty-pulse' : ''}`}
        onClick={() => sensors.length > 0 && setSelectedSensor(sensors[0])}
        style={{ cursor: sensors.length > 0 ? 'pointer' : 'default' }}
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

        {/* Sensor badges (all sensors at this location) */}
        {sensors.length > 0 && (
          <g className="sensor-badges">
            {sensors.slice(0, 4).map((s, idx) => {
              const voltage = s.sensor_id.startsWith('VS-') ? getVoltageForSensor(s.sensor_id) : null;
              const badgeY = node.y - 6 + idx * 14;
              return (
                <g key={s.sensor_id} transform={`translate(${node.x + 30}, ${badgeY})`}>
                  <rect
                    x={-2}
                    y={-9}
                    rx={4}
                    ry={4}
                    width={70}
                    height={16}
                    fill="rgba(30, 144, 255, 0.15)"
                    stroke={s.is_operational ? '#4caf50' : '#ff5252'}
                    strokeWidth="1"
                  />
                  <text
                    x={2}
                    y={2}
                    className="sensor-value"
                    fill="#ffffff"
                    fontSize="10"
                  >
                    {s.sensor_id}{voltage ? ` · ${voltage}V` : ''}
                  </text>
                </g>
              );
            })}
          </g>
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
            <button className="modal-close" onClick={() => setSelectedSensor(null)}>
              ✕
            </button>
            <h3>Sensor Details</h3>
            <div className="modal-body">
              <div className="detail-section">
                <strong>Sensor ID:</strong> {selectedSensor.sensor_id}
              </div>
              <div className="detail-section">
                <strong>Location:</strong> {selectedSensor.location}
              </div>
              <div className="detail-section">
                <strong>Status:</strong>{' '}
                <span
                  style={{
                    color: selectedSensor.is_operational ? '#4caf50' : '#ff5252',
                    fontWeight: 'bold',
                  }}
                >
                  {selectedSensor.is_operational ? '✅ Operational' : '❌ Faulty'}
                </span>
              </div>
              {selectedSensor.sensor_id.startsWith('VS-') && (() => {
                const voltage = voltageData.find((v) => v.sensor_id === selectedSensor.sensor_id);
                return voltage ? (
                  <>
                    <div className="detail-section">
                      <strong>Voltage L1:</strong> {(voltage.voltage_l1 || 0).toFixed(2)}V
                    </div>
                    <div className="detail-section">
                      <strong>Voltage L2:</strong> {(voltage.voltage_l2 || 0).toFixed(2)}V
                    </div>
                    <div className="detail-section">
                      <strong>Voltage L3:</strong> {(voltage.voltage_l3 || 0).toFixed(2)}V
                    </div>
                    <div className="detail-section">
                      <strong>Frequency:</strong> {(voltage.frequency || 0).toFixed(2)} Hz
                    </div>
                  </>
                ) : null;
              })()}
              <div className="detail-section">
                <strong>Last Update:</strong> {selectedSensor.seconds_since_update}s ago
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GridTopology;
