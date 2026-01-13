import React from 'react';
import PropTypes from 'prop-types';
import './GridStats.css';

const GridStats = ({ stats, sensorStatus = [] }) => {
  const activeSensors = sensorStatus.filter(s => s.is_operational).length;
  const totalSensors = sensorStatus.length;
  
  return (
    <div className="grid-stats">
      <div className="stat-card">
        <div className="stat-icon">🔌</div>
        <div className="stat-content">
          <div className="stat-value">{activeSensors} / {totalSensors}</div>
          <div className="stat-label">Active Sensors</div>
          {totalSensors > 0 && (
            <div className="stat-subtext">
              {Math.round((activeSensors / totalSensors) * 100)}% operational
            </div>
          )}
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">⚠️</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_faults_24h || 0}</div>
          <div className="stat-label">Total Faults (24h)</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">📊</div>
        <div className="stat-content">
          <div className="stat-value">{stats.quality_violations || 0}</div>
          <div className="stat-label">Quality Violations</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">⚡</div>
        <div className="stat-content">
          <div className="stat-value">{stats.avg_voltage?.toFixed(1) || '—'} V</div>
          <div className="stat-label">Avg. Voltage (24h)</div>
        </div>
      </div>
    </div>
  );
};

GridStats.propTypes = {
  stats: PropTypes.shape({
    total_faults_24h: PropTypes.number,
    quality_violations: PropTypes.number,
    avg_voltage: PropTypes.number,
  }).isRequired,
  sensorStatus: PropTypes.arrayOf(
    PropTypes.shape({
      sensor_id: PropTypes.string,
      is_operational: PropTypes.bool,
    })
  ),
};

GridStats.defaultProps = {
  sensorStatus: [],
};

export default GridStats;
