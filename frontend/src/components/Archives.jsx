import React, { useEffect, useState } from 'react';
import './Archives.css';

const Archives = ({ token }) => {
  const isPages =
    typeof window !== 'undefined' && window.location.hostname.endsWith('github.io');
  const DEMO =
    typeof import.meta.env.VITE_DEMO_MODE !== 'undefined'
      ? import.meta.env.VITE_DEMO_MODE === 'true'
      : isPages;
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchArchives = async () => {
    if (DEMO) {
      setError('');
      setFiles([
        { key: 'exports/voltage_demo.json', size: 1024, modified: new Date().toISOString() },
        { key: 'exports/faults_demo.csv', size: 2048, modified: new Date().toISOString() },
      ]);
      return;
    }
    if (!token) {
      setError('Login required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/export/list', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (!response.ok || result.status === 'error') {
        const detail = result.message || response.statusText;
        setError(`Failed to load archives: ${detail}`);
        setFiles([]);
      } else {
        setFiles(result.files || []);
      }
    } catch (err) {
      setError(`Failed to load archives: ${err.message}`);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArchives();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const downloadFile = async (key) => {
    if (DEMO) {
      // In demo mode, just show a placeholder download
      const blob = new Blob([
        key.endsWith('.json') ? JSON.stringify({ demo: true }, null, 2) : 'demo,data\n1,2\n',
      ], { type: key.endsWith('.json') ? 'application/json' : 'text/csv' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      return;
    }
    if (!token) return;
    try {
      const safeKey = encodeURIComponent(key).replace(/%2F/g, '/');
      const response = await fetch(`/api/export/${safeKey}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (response.ok && result.status === 'success' && result.url) {
        window.open(result.url, '_blank');
      } else {
        const detail = result.message || response.statusText;
        setError(`Download failed: ${detail}`);
      }
    } catch (err) {
      setError(`Download failed: ${err.message}`);
    }
  };

  return (
    <div className="archives">
      <div className="archives-header">
        <h2>📁 Data Archives</h2>
        <button onClick={fetchArchives} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      {error && <div className="archives-error">{error}</div>}
      <div className="archives-table">
        <div className="archives-row archives-head">
          <div>Filename</div>
          <div>Size (bytes)</div>
          <div>Modified</div>
          <div>Actions</div>
        </div>
        {files.length === 0 && !loading && (
          <div className="archives-row">
            <div colSpan={4}>No exports yet</div>
          </div>
        )}
        {files.map((file) => (
          <div className="archives-row" key={file.key}>
            <div className="archives-key">{file.key}</div>
            <div>{file.size}</div>
            <div>{file.modified}</div>
            <div>
              <button onClick={() => downloadFile(file.key)}>Download</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Archives;
