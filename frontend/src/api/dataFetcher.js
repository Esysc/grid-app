import { graphqlClient } from './graphqlClient';
import {
  VOLTAGE_READINGS_QUERY,
  POWER_QUALITY_QUERY,
  FAULT_EVENTS_QUERY,
  SENSOR_STATS_QUERY
} from './queries';

/**
 * Unified data fetcher that supports both REST and GraphQL
 * Provides a consistent interface for fetching data regardless of the underlying protocol
 */
export class DataFetcher {
  constructor(token, useGraphQL = false) {
    this.token = token;
    this.useGraphQL = useGraphQL;
    
    if (useGraphQL) {
      graphqlClient.setToken(token);
    }
  }

  /**
   * Update the API mode (REST or GraphQL)
   */
  setMode(useGraphQL) {
    this.useGraphQL = useGraphQL;
    if (useGraphQL) {
      graphqlClient.setToken(this.token);
    }
  }

  /**
   * Update the authentication token
   */
  setToken(token) {
    this.token = token;
    if (this.useGraphQL) {
      graphqlClient.setToken(token);
    }
  }

  /**
   * Fetch voltage readings
   * @param {number} limit - Number of readings to fetch
   * @param {string} sensorId - Optional sensor ID filter
   * @returns {Promise<Array>} Voltage readings
   */
  async fetchVoltage(limit = 30, sensorId = null) {
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(VOLTAGE_READINGS_QUERY, {
          limit,
          sensorId,
          hours: 24
        });
        // Transform GraphQL response to match REST format
        return data.voltageReadings.map(reading => ({
          id: reading.id,
          sensor_id: reading.sensorId,
          location: reading.location,
          voltage_l1: reading.voltageL1,
          voltage_l2: reading.voltageL2,
          voltage_l3: reading.voltageL3,
          frequency: reading.frequency,
          timestamp: reading.timestamp
        }));
      } catch (error) {
        if (error.message === 'TOKEN_EXPIRED') {
          throw new Error('TOKEN_EXPIRED');
        }
        console.error('GraphQL voltage fetch error:', error);
        throw error;
      }
    } else {
      // REST API
      const url = sensorId 
        ? `/api/sensors/voltage?limit=${limit}&sensor_id=${sensorId}`
        : `/api/sensors/voltage?limit=${limit}`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (response.status === 401) {
        throw new Error('TOKEN_EXPIRED');
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    }
  }

  /**
   * Fetch power quality metrics
   * @param {number} limit - Number of metrics to fetch
   * @param {string} sensorId - Optional sensor ID filter
   * @returns {Promise<Array>} Power quality metrics
   */
  async fetchPowerQuality(limit = 20, sensorId = null) {
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(POWER_QUALITY_QUERY, {
          limit,
          sensorId,
          hours: 24
        });
        // Transform GraphQL response to match REST format
        return data.powerQuality.map(metric => ({
          id: metric.id,
          sensor_id: metric.sensorId,
          location: metric.location,
          thd_voltage: metric.thdVoltage,
          thd_current: metric.thdCurrent,
          power_factor: metric.powerFactor,
          voltage_imbalance: metric.voltageImbalance,
          flicker_severity: metric.flickerSeverity,
          timestamp: metric.timestamp
        }));
      } catch (error) {
        if (error.message === 'TOKEN_EXPIRED') {
          throw new Error('TOKEN_EXPIRED');
        }
        console.error('GraphQL power quality fetch error:', error);
        throw error;
      }
    } else {
      // REST API
      const url = sensorId
        ? `/api/sensors/power-quality?limit=${limit}&sensor_id=${sensorId}`
        : `/api/sensors/power-quality?limit=${limit}`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (response.status === 401) {
        throw new Error('TOKEN_EXPIRED');
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    }
  }

  /**
   * Fetch fault events
   * @param {number} limit - Number of faults to fetch
   * @param {string} severity - Optional severity filter
   * @returns {Promise<Array>} Fault events
   */
  async fetchFaults(limit = 10, severity = null) {
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(FAULT_EVENTS_QUERY, {
          limit,
          severity,
          hours: 24
        });
        // Transform GraphQL response to match REST format
        return data.faultEvents.map(fault => ({
          id: fault.id,
          event_id: fault.eventId,
          severity: fault.severity,
          fault_type: fault.eventType,
          location: fault.location,
          timestamp: fault.timestamp,
          duration_ms: fault.durationMs,
          resolved: fault.resolved,
          resolved_at: fault.resolvedAt
        }));
      } catch (error) {
        if (error.message === 'TOKEN_EXPIRED') {
          throw new Error('TOKEN_EXPIRED');
        }
        console.error('GraphQL faults fetch error:', error);
        throw error;
      }
    } else {
      // REST API
      const response = await fetch('/api/faults/recent', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (response.status === 401) {
        throw new Error('TOKEN_EXPIRED');
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    }
  }

  /**
   * Fetch sensor statistics
   * @returns {Promise<Object>} Sensor statistics
   */
  async fetchStats() {
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(SENSOR_STATS_QUERY);
        // Transform GraphQL response to match REST format
        return {
          total_sensors: data.sensorStats.totalSensors,
          active_sensors: data.sensorStats.activeSensors,
          total_faults_24h: data.sensorStats.faultCount24h,
          violations: data.sensorStats.violationCount24h,
          avg_voltage: data.sensorStats.avgVoltage,
          min_voltage: data.sensorStats.minVoltage,
          max_voltage: data.sensorStats.maxVoltage
        };
      } catch (error) {
        if (error.message === 'TOKEN_EXPIRED') {
          throw new Error('TOKEN_EXPIRED');
        }
        console.error('GraphQL stats fetch error:', error);
        throw error;
      }
    } else {
      // REST API
      const response = await fetch('/api/sensors/stats', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (response.status === 401) {
        throw new Error('TOKEN_EXPIRED');
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    }
  }

  /**
   * Fetch sensor status (REST only for now)
   * @returns {Promise<Array>} Sensor status
   */
  async fetchSensorStatus() {
    // This endpoint doesn't have a GraphQL equivalent yet, always use REST
    const response = await fetch('/api/sensors/status', {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    if (response.status === 401) {
      throw new Error('TOKEN_EXPIRED');
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }
}
