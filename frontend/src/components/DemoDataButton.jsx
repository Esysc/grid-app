import React, { useState, useEffect } from 'react';
import './DemoDataButton.css';

const DemoDataButton = ({ token }) => {
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [message, setMessage] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const handlePopulate = async () => {
    if (!token || loading || cooldown > 0) return;

    setShowConfirm(false);
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('/api/simulate/populate?hours=24', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const result = await response.json();

      if (!response.ok) {
        const detail = result.detail || result.message || response.statusText;
        setMessage(`❌ ${detail}`);
        return;
      }

      setMessage(
        `✅ Generated ${result.voltage_readings || 0} voltage readings, ${
          result.power_quality_metrics || 0
        } power quality metrics, ${result.fault_events || 0} fault events`
      );
      setCooldown(30);
    } catch (err) {
      setMessage(`❌ Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="demo-data-button-wrapper">
        <button
          className="demo-data-button"
          onClick={() => setShowConfirm(true)}
          disabled={loading || cooldown > 0 || !token}
          title={
            cooldown > 0
              ? `Wait ${cooldown}s before next load`
              : 'Loads simulated historical data for testing and demonstrations'
          }
        >
          {loading ? (
            <>
              <span className="demo-data-spinner"></span> Loading...
            </>
          ) : cooldown > 0 ? (
            `Wait ${cooldown}s`
          ) : (
            '📊 Load Simulated Static Data'
          )}
        </button>
        {message && (
          <div className={`demo-data-message ${message.startsWith('✅') ? 'success' : 'error'}`}>
            {message}
          </div>
        )}
      </div>

      {showConfirm && (
        <div className="demo-data-confirm-overlay" onClick={() => setShowConfirm(false)}>
          <div className="demo-data-confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Load Simulated Static Data?</h3>
            <p>This will insert 24 hours of simulated historical data into the database for testing. Live MQTT sensor data will continue running in parallel.</p>
            <div className="demo-data-confirm-actions">
              <button className="demo-data-confirm-cancel" onClick={() => setShowConfirm(false)}>
                Cancel
              </button>
              <button className="demo-data-confirm-proceed" onClick={handlePopulate}>
                Load Data
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DemoDataButton;
