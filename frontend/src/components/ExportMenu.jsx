import React, { useState, useEffect, useRef } from 'react';
import './ExportMenu.css';

const ExportMenu = ({ token, onViewArchives }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open]);

  const callExport = async (path) => {
    if (!token) {
      setMessage('Login required');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`/api${path}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const result = await response.json();
      if (!response.ok || result.status === 'error') {
        const detail = result.message || response.statusText;
        setMessage(`Export failed: ${detail}`);
      } else {
        const location = result.location || 'S3 export completed';
        setMessage(`Success: ${location}`);
      }
    } catch (err) {
      setMessage(`Export failed: ${err.message}`);
    } finally {
      setLoading(false);
      setOpen(false);
    }
  };

  return (
    <div className="export-menu" ref={menuRef}>
      <button
        className="export-trigger"
        onClick={() => setOpen((prev) => !prev)}
        disabled={loading}
      >
        {loading ? 'Exporting…' : 'Export ▼'}
      </button>
      {open && (
        <div className="export-dropdown">
          <button onClick={() => callExport('/export/voltage?hours=24')} disabled={loading}>
            Export Voltage Data (24h)
          </button>
          <button onClick={() => callExport('/export/faults?hours=24')} disabled={loading}>
            Export Fault Events (24h)
          </button>
          <button onClick={onViewArchives} disabled={loading}>
            View Archives
          </button>
        </div>
      )}
      {message && <div className="export-message">{message}</div>}
    </div>
  );
};

export default ExportMenu;
