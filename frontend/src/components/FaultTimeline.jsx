import React from 'react';
import './FaultTimeline.css';

const FaultTimeline = ({ faults }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#e53e3e';
      case 'high': return '#ed8936';
      case 'medium': return '#ecc94b';
      case 'low': return '#48bb78';
      default: return '#a0aec0';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="fault-timeline">
      {(!Array.isArray(faults) || faults.length === 0) ? (
        <div className="no-faults">
          <p>✅ No recent faults detected</p>
        </div>
      ) : (
        <div className="fault-list">
          {faults.map((fault, index) => (
            <div 
              key={fault.id || index} 
              className="fault-item"
              style={{ borderLeftColor: getSeverityColor(fault.severity) }}
            >
              <div className="fault-header">
                <span className="fault-sensor">
                  Sensor {fault.sensor_id}
                </span>
                <span 
                  className="fault-severity"
                  style={{ backgroundColor: getSeverityColor(fault.severity) }}
                >
                  {fault.severity}
                </span>
              </div>
              <div className="fault-description">
                {fault.fault_type}
              </div>
              <div className="fault-footer">
                <span className="fault-location">
                  📍 {fault.location || 'Unknown'}
                </span>
                <span className="fault-time">
                  🕐 {formatTimestamp(fault.timestamp)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FaultTimeline;
