import React, { useState, useEffect, useRef } from 'react';
import './ExportMenu.css';

const ExportMenu = ({ token, onViewArchives, onTokenExpired }) => {
  const isPages =
    typeof window !== 'undefined' && window.location.hostname.endsWith('github.io');
  const DEMO =
    typeof import.meta.env.VITE_DEMO_MODE !== 'undefined'
      ? import.meta.env.VITE_DEMO_MODE === 'true'
      : isPages;
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
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

  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
    return () => clearTimeout(timer);
  }, [message]);

  const callExport = async (path) => {
    if (DEMO) {
      setMessage('Demo mode: simulated export complete');
      setMessageType('success');
      setOpen(false);
      return;
    }
    if (!token) {
      setMessage('Login required');
      setMessageType('error');
      return;
    }
    setLoading(true);
    setMessage('');
    setMessageType('');
    try {
      const response = await fetch(`/api${path}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.status === 401) {
        onTokenExpired?.();
        return;
      }
      const result = await response.json();
      if (!response.ok || result.status === 'error') {
        const detail = result.message || response.statusText;
        setMessage(`Export failed: ${detail}`);
        setMessageType('error');
      } else {
        const location = result.location || 'S3 export completed';
        setMessage(`Success: ${location}`);
        setMessageType('success');
      }
    } catch (err) {
      setMessage(`Export failed: ${err.message}`);
      setMessageType('error');
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
      {message && <div className={`export-message ${messageType}`}>{message}</div>}
    </div>
  );
};

export default ExportMenu;
