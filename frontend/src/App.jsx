import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import PowerQualityChart from './components/PowerQualityChart';
import FaultTimeline from './components/FaultTimeline';
import GridStats from './components/GridStats';
import GridTopology from './components/GridTopology';
import ExportMenu from './components/ExportMenu';
import Archives from './components/Archives';
import DemoBanner from './components/DemoBanner';
import DemoDataButton from './components/DemoDataButton';

function App() {
  const isPages =
    typeof window !== 'undefined' && window.location.hostname.endsWith('github.io');
  const DEMO =
    typeof import.meta.env.VITE_DEMO_MODE !== 'undefined'
      ? import.meta.env.VITE_DEMO_MODE === 'true'
      : isPages;
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [recentFaults, setRecentFaults] = useState([]);
  const [powerQuality, setPowerQuality] = useState([]);
  const [voltageData, setVoltageData] = useState([]);
  const [stats, setStats] = useState({ total_sensors: 0, total_faults_24h: 0, violations: 0 });
  const [accessToken, setAccessToken] = useState(null);
  const [view, setView] = useState('dashboard');
  const eventSourceRef = useRef(null);

  useEffect(() => {
    // Check if user is already logged in (token in localStorage)
    const savedToken = localStorage.getItem('accessToken');
    if (DEMO) {
      const demoToken = 'demo-token';
      setAccessToken(demoToken);
      setIsAuthenticated(true);
      startDataFetch(demoToken);
    } else if (savedToken) {
      setAccessToken(savedToken);
      setIsAuthenticated(true);
      startDataFetch(savedToken);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      if (DEMO) {
        const token = 'demo-token';
        setAccessToken(token);
        localStorage.setItem('accessToken', token);
        setIsAuthenticated(true);
        setUsername('');
        setPassword('');
        startDataFetch(token);
        return;
      }
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const token = data.access_token;
        setAccessToken(token);
        localStorage.setItem('accessToken', token);
        setIsAuthenticated(true);
        setUsername('');
        setPassword('');
        startDataFetch(token);
      } else {
        alert('Login failed: Invalid credentials');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed: ' + error.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    setAccessToken(null);
    setIsAuthenticated(false);
    setRecentFaults([]);
    setPowerQuality([]);
    setVoltageData([]);
    setStats({ total_sensors: 0, total_faults_24h: 0, violations: 0 });
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const startDataFetch = (token) => {
    if (DEMO) {
      // Seed synthetic demo data
      const now = Date.now();
      const makeTs = (i) => new Date(now - i * 1000 * 30).toISOString();
      setVoltageData(
        Array.from({ length: 30 }, (_, i) => ({
          timestamp: makeTs(30 - i),
          voltage_l1: 225 + Math.sin(i / 3) * 3,
        }))
      );
      setPowerQuality(
        Array.from({ length: 20 }, (_, i) => ({
          timestamp: makeTs(20 - i),
          thd_voltage: 2 + Math.cos(i / 4),
        }))
      );
      setRecentFaults([
        {
          id: 'FT-001',
          sensor_id: 'FT-DEMO-1',
          fault_type: 'overvoltage',
          severity: 'medium',
          location: 'Demo Substation',
          timestamp: new Date(now - 1000 * 60 * 15).toISOString(),
        },
      ]);
      setStats({ total_sensors: 12, total_faults_24h: 1, violations: 0 });
      // No SSE in demo mode
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    fetchFaults(token);
    fetchPowerQuality(token);
    fetchVoltage(token);
    fetchStats(token);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    const eventSource = new EventSource('/api/stream');
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.voltage) {
          setVoltageData((prev) => [...prev, data.voltage].slice(-30));
        }
        if (data.power_quality) {
          setPowerQuality((prev) => [...prev, data.power_quality].slice(-20));
        }
        if (data.fault) {
          setRecentFaults((prev) => [data.fault, ...prev].slice(0, 10));
        }
      } catch (e) {
        console.error('Error parsing SSE data:', e);
      }
    });
  };

  const fetchFaults = async (token) => {
    try {
      const response = await fetch('/api/faults/recent', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setRecentFaults(data);
      }
    } catch (error) {
      console.error('Error fetching faults:', error);
    }
  };

  const fetchPowerQuality = async (token) => {
    try {
      const response = await fetch('/api/sensors/power-quality?limit=20', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPowerQuality(data);
      }
    } catch (error) {
      console.error('Error fetching power quality:', error);
    }
  };

  const fetchVoltage = async (token) => {
    try {
      const response = await fetch('/api/sensors/voltage?limit=30', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setVoltageData(data);
      }
    } catch (error) {
      console.error('Error fetching voltage:', error);
    }
  };

  const fetchStats = async (token) => {
    try {
      const response = await fetch('/api/stats', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="App login-page">
        <header className="App-header">
          <h1>⚡ Grid Monitor</h1>
          <p>Secure Grid Monitoring & Analytics Platform</p>
        </header>

        <div className="login-container">
          <h2>Login</h2>
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="username">Username:</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="secret"
                required
              />
            </div>
            <button type="submit">Login</button>
          </form>
          <p className="login-hint">Demo: username: <strong>admin</strong>, password: <strong>secret</strong></p>
        </div>

        <footer className="App-footer">
          <p>Grid Monitor - Real-time Grid Analytics</p>
        </footer>
      </div>
    );
  }

  return (
    <div className="App">
      <DemoBanner isDemo={DEMO} />
      <header className="App-header">
        <div>
          <h1>⚡ Grid Monitor</h1>
          <p>Grid Monitoring & Analytics Platform</p>
        </div>
        <div className="header-actions">
          <nav className="nav-tabs">
            <button
              className={view === 'dashboard' ? 'active' : ''}
              onClick={() => setView('dashboard')}
            >
              Dashboard
            </button>
            <button
              className={view === 'archives' ? 'active' : ''}
              onClick={() => setView('archives')}
            >
              Archives
            </button>
          </nav>
          {isAuthenticated && <DemoDataButton token={accessToken} />}
          <ExportMenu token={accessToken} onViewArchives={() => setView('archives')} />
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {view === 'dashboard' && (
        <>
          <GridStats stats={stats} />
          <GridTopology />
          <div className="dashboard-grid">
            <div className="chart-container">
              <h2>⚡ Voltage Monitoring</h2>
              <PowerQualityChart
                data={voltageData}
                dataKey="voltage_l1"
                yAxisLabel="Voltage (V)"
                color="#8884d8"
              />
            </div>

            <div className="chart-container">
              <h2>📊 Power Quality</h2>
              <PowerQualityChart
                data={powerQuality}
                dataKey="thd_voltage"
                yAxisLabel="THD (%)"
                color="#82ca9d"
              />
            </div>

            <div className="fault-container">
              <h2>⚠️ Recent Faults</h2>
              <FaultTimeline faults={recentFaults} />
            </div>
          </div>
        </>
      )}

      {view === 'archives' && (
        <div className="archives-section">
          <Archives token={accessToken} />
        </div>
      )}

      <footer className="App-footer">
        <p>Grid Monitor - Real-time Grid Analytics</p>
      </footer>
    </div>
  );
}

export default App;
