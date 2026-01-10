import React from 'react';
import PropTypes from 'prop-types';
import './GridStats.css';

const GridStats = ({ stats }) => {
  return (
    <div className="grid-stats">
      <div className="stat-card">
        <div className="stat-icon">🔌</div>
        <div className="stat-content">
          <div className="stat-value">{stats.active_sensors || 0}</div>
          <div className="stat-label">Active Sensors</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">⚠️</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_faults_24h || 0}</div>
          <div className="stat-label">Total Faults</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">📊</div>
        <div className="stat-content">
          <div className="stat-value">{stats.quality_violations || 0}</div>
          <div className="stat-label">Quality Violations</div>
        </div>
      </div>
    </div>
  );
};

GridStats.propTypes = {
  stats: PropTypes.shape({
    active_sensors: PropTypes.number,
    total_faults_24h: PropTypes.number,
    quality_violations: PropTypes.number,
  }).isRequired,
};

export default GridStats;
