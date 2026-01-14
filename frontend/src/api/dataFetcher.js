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
  constructor(token, useGraphQL = false, logCallback = null) {
    this.token = token;
    this.useGraphQL = useGraphQL;
    this.logCallback = logCallback;
    this.requestCounter = 0;
    
    if (useGraphQL) {
      graphqlClient.setToken(token);
    }
  }

  log(endpoint, method, status, requestData = null, response = null, error = null, duration = null) {
    if (this.logCallback) {
      this.logCallback({
        id: ++this.requestCounter,
        endpoint,
        method,
        status,
        requestData,
        response,
        error,
        duration,
        timestamp: Date.now()
      });
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
    const startTime = Date.now();
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(VOLTAGE_READINGS_QUERY, {
          limit,
          sensorId,
          hours: 24
        });
        const duration = Date.now() - startTime;
        // Transform GraphQL response to match REST format
        if (!data.voltageReadings || !Array.isArray(data.voltageReadings)) {
          this.log('/graphql', 'GraphQL', 'error', { query: 'voltageReadings', limit, sensorId }, null, 'Invalid voltage data received', duration);
          throw new Error('Invalid voltage data received');
        }
        const result = data.voltageReadings.map(reading => ({
          id: reading.id,
          sensor_id: reading.sensorId,
          location: reading.location,
          voltage_l1: reading.voltageL1,
          voltage_l2: reading.voltageL2,
          voltage_l3: reading.voltageL3,
          frequency: reading.frequency,
          timestamp: reading.timestamp
        }));
        this.log('/graphql', 'GraphQL', 'success', { query: 'voltageReadings', limit, sensorId }, { count: result.length }, null, duration);
        return result;
      } catch (error) {
        const duration = Date.now() - startTime;
        this.log('/graphql', 'GraphQL', 'error', { query: 'voltageReadings', limit, sensorId }, null, error.message, duration);
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
      const startTime = Date.now();
      
      try {
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        const duration = Date.now() - startTime;
        
        if (response.status === 401) {
          this.log(url, 'GET', 'error', null, null, 'TOKEN_EXPIRED', duration);
          throw new Error('TOKEN_EXPIRED');
        }
        
        if (!response.ok) {
          this.log(url, 'GET', 'error', null, null, `HTTP ${response.status}`, duration);
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.log(url, 'GET', 'success', null, { count: data.length }, null, duration);
        return data;
      } catch (error) {
        const duration = Date.now() - startTime;
        if (!error.message.includes('TOKEN_EXPIRED') && !error.message.includes('HTTP')) {
          this.log(url, 'GET', 'error', null, null, error.message, duration);
        }
        throw error;
      }
    }
  }

  /**
   * Fetch power quality metrics
   * @param {number} limit - Number of metrics to fetch
   * @param {string} sensorId - Optional sensor ID filter
   * @returns {Promise<Array>} Power quality metrics
   */
  async fetchPowerQuality(limit = 20, sensorId = null) {
    const startTime = Date.now();
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(POWER_QUALITY_QUERY, {
          limit,
          sensorId,
          hours: 24
        });
        const duration = Date.now() - startTime;
        // Transform GraphQL response to match REST format
        if (!data.powerQuality || !Array.isArray(data.powerQuality)) {
          this.log('/graphql', 'GraphQL', 'error', { query: 'powerQuality', limit, sensorId }, null, 'Invalid power quality data received', duration);
          throw new Error('Invalid power quality data received');
        }
        const result = data.powerQuality.map(metric => ({
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
        this.log('/graphql', 'GraphQL', 'success', { query: 'powerQuality', limit, sensorId }, { count: result.length }, null, duration);
        return result;
      } catch (error) {
        const duration = Date.now() - startTime;
        this.log('/graphql', 'GraphQL', 'error', { query: 'powerQuality', limit, sensorId }, null, error.message, duration);
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
      const startTime = Date.now();
      
      try {
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        const duration = Date.now() - startTime;
        
        if (response.status === 401) {
          this.log(url, 'GET', 'error', null, null, 'TOKEN_EXPIRED', duration);
          throw new Error('TOKEN_EXPIRED');
        }
        
        if (!response.ok) {
          this.log(url, 'GET', 'error', null, null, `HTTP ${response.status}`, duration);
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.log(url, 'GET', 'success', null, { count: data.length }, null, duration);
        return data;
      } catch (error) {
        const duration = Date.now() - startTime;
        if (!error.message.includes('TOKEN_EXPIRED') && !error.message.includes('HTTP')) {
          this.log(url, 'GET', 'error', null, null, error.message, duration);
        }
        throw error;
      }
    }
  }

  /**
   * Fetch fault events
   * @param {number} limit - Number of faults to fetch
   * @param {string} severity - Optional severity filter
   * @returns {Promise<Array>} Fault events
   */
  async fetchFaults(limit = 10, severity = null) {
    const startTime = Date.now();
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(FAULT_EVENTS_QUERY, {
          limit,
          severity,
          hours: 24
        });
        const duration = Date.now() - startTime;
        // Transform GraphQL response to match REST format
        if (!data.faultEvents || !Array.isArray(data.faultEvents)) {
          this.log('/graphql', 'GraphQL', 'error', { query: 'faultEvents', limit, severity }, null, 'Invalid fault events data received', duration);
          throw new Error('Invalid fault events data received');
        }
        const result = data.faultEvents.map(fault => ({
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
        this.log('/graphql', 'GraphQL', 'success', { query: 'faultEvents', limit, severity }, { count: result.length }, null, duration);
        return result;
      } catch (error) {
        const duration = Date.now() - startTime;
        this.log('/graphql', 'GraphQL', 'error', { query: 'faultEvents', limit, severity }, null, error.message, duration);
        if (error.message === 'TOKEN_EXPIRED') {
          throw new Error('TOKEN_EXPIRED');
        }
        console.error('GraphQL faults fetch error:', error);
        throw error;
      }
    } else {
      // REST API
      const url = '/api/faults/recent';
      const startTime = Date.now();
      
      try {
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        const duration = Date.now() - startTime;
        
        if (response.status === 401) {
          this.log(url, 'GET', 'error', null, null, 'TOKEN_EXPIRED', duration);
          throw new Error('TOKEN_EXPIRED');
        }
        
        if (!response.ok) {
          this.log(url, 'GET', 'error', null, null, `HTTP ${response.status}`, duration);
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.log(url, 'GET', 'success', null, { count: data.length }, null, duration);
        return data;
      } catch (error) {
        const duration = Date.now() - startTime;
        if (!error.message.includes('TOKEN_EXPIRED') && !error.message.includes('HTTP')) {
          this.log(url, 'GET', 'error', null, null, error.message, duration);
        }
        throw error;
      }
    }
  }

  /**
   * Fetch sensor statistics
   * @returns {Promise<Object>} Sensor statistics
   */
  async fetchStats() {
    const startTime = Date.now();
    if (this.useGraphQL) {
      try {
        const data = await graphqlClient.request(SENSOR_STATS_QUERY);
        const duration = Date.now() - startTime;
        // Transform GraphQL response to match REST format
        if (!data.sensorStats) {
          this.log('/graphql', 'GraphQL', 'error', { query: 'sensorStats' }, null, 'Invalid sensor stats data received', duration);
          throw new Error('Invalid sensor stats data received');
        }
        const result = {
          total_sensors: data.sensorStats.totalSensors,
          active_sensors: data.sensorStats.activeSensors,
          offline_sensors: data.sensorStats.offlineSensors,
          total_faults_24h: data.sensorStats.faultCount24h,
          quality_violations: data.sensorStats.violationCount24h,
          avg_voltage: data.sensorStats.avgVoltage,
          avg_power_factor: data.sensorStats.avgPowerFactor,
          min_voltage: data.sensorStats.minVoltage,
          max_voltage: data.sensorStats.maxVoltage
        };
        this.log('/graphql', 'GraphQL', 'success', { query: 'sensorStats' }, result, null, duration);
        return result;
      } catch (error) {
        const duration = Date.now() - startTime;
        this.log('/graphql', 'GraphQL', 'error', { query: 'sensorStats' }, null, error.message, duration);
        if (error.message === 'TOKEN_EXPIRED') {
          throw new Error('TOKEN_EXPIRED');
        }
        console.error('GraphQL stats fetch error:', error);
        throw error;
      }
    } else {
      // REST API
      const url = '/api/sensors/stats';
      const startTime = Date.now();
      
      try {
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        const duration = Date.now() - startTime;
        
        if (response.status === 401) {
          this.log(url, 'GET', 'error', null, null, 'TOKEN_EXPIRED', duration);
          throw new Error('TOKEN_EXPIRED');
        }
        
        if (!response.ok) {
          this.log(url, 'GET', 'error', null, null, `HTTP ${response.status}`, duration);
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.log(url, 'GET', 'success', null, data, null, duration);
        return data;
      } catch (error) {
        const duration = Date.now() - startTime;
        if (!error.message.includes('TOKEN_EXPIRED') && !error.message.includes('HTTP')) {
          this.log(url, 'GET', 'error', null, null, error.message, duration);
        }
        throw error;
      }
    }
  }

  /**
   * Fetch sensor status (REST only for now)
   * @returns {Promise<Array>} Sensor status
   */
  async fetchSensorStatus() {
    // This endpoint doesn't have a GraphQL equivalent yet, always use REST
    const url = '/api/sensors/status';
    const startTime = Date.now();
    
    try {
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      const duration = Date.now() - startTime;
      
      if (response.status === 401) {
        this.log(url, 'GET', 'error', null, null, 'TOKEN_EXPIRED', duration);
        throw new Error('TOKEN_EXPIRED');
      }
      
      if (!response.ok) {
        this.log(url, 'GET', 'error', null, null, `HTTP ${response.status}`, duration);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      this.log(url, 'GET', 'success', null, { count: data.length }, null, duration);
      return data;
    } catch (error) {
      const duration = Date.now() - startTime;
      if (!error.message.includes('TOKEN_EXPIRED') && !error.message.includes('HTTP')) {
        this.log(url, 'GET', 'error', null, null, error.message, duration);
      }
      throw error;
    }
  }
}
