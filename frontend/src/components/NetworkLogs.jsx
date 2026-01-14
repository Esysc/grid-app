import React, { useState } from 'react';
import './NetworkLogs.css';

function NetworkLogs({ logs, isExpanded, onToggle }) {
  const [selectedLog, setSelectedLog] = useState(null);

  const getStatusClass = (status) => {
    if (status === 'success') return 'log-success';
    if (status === 'error') return 'log-error';
    return 'log-pending';
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    return `${ms}ms`;
  };

  return (
    <div className={`network-logs ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="network-logs-header" onClick={onToggle}>
        <span className="network-logs-title">🌐 Network Logs</span>
        <span className="network-logs-count">{logs.length} requests</span>
        <span className="network-logs-toggle">{isExpanded ? '▼' : '▲'}</span>
      </div>
      
      {isExpanded && (
        <div className="network-logs-content">
          <div className="network-logs-list">
            {logs.length === 0 ? (
              <div className="no-logs">No network requests yet</div>
            ) : (
              logs.slice().reverse().map((log) => (
                <div
                  key={log.id}
                  className={`network-log-item ${getStatusClass(log.status)} ${selectedLog?.id === log.id ? 'selected' : ''}`}
                  onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                >
                  <div className="log-summary">
                    <span className={`log-method ${log.method}`}>{log.method}</span>
                    <span className="log-endpoint">{log.endpoint}</span>
                    <span className="log-time">{formatTime(log.timestamp)}</span>
                    <span className="log-duration">{formatDuration(log.duration)}</span>
                    <span className={`log-status ${log.status}`}>
                      {log.status === 'success' ? '✓' : log.status === 'error' ? '✗' : '⋯'}
                    </span>
                  </div>
                  
                  {selectedLog?.id === log.id && (
                    <div className="log-details">
                      <div className="log-detail-section">
                        <strong>Request:</strong>
                        {log.requestData && (
                          <pre>{JSON.stringify(log.requestData, null, 2)}</pre>
                        )}
                      </div>
                      {log.response && (
                        <div className="log-detail-section">
                          <strong>Response:</strong>
                          <pre>{JSON.stringify(log.response, null, 2)}</pre>
                        </div>
                      )}
                      {log.error && (
                        <div className="log-detail-section log-error-detail">
                          <strong>Error:</strong>
                          <pre>{log.error}</pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default NetworkLogs;
