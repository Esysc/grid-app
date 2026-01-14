/**
 * GraphQL queries and mutations for Grid Monitor API
 * Mirrors the REST API endpoints with GraphQL equivalents
 */

// Query for voltage readings
export const VOLTAGE_READINGS_QUERY = `
  query VoltageReadings($limit: Int, $sensorId: String, $hours: Int) {
    voltageReadings(options: { limit: $limit, sensorId: $sensorId, timeRange: { hours: $hours } }) {
      id
      sensorId
      location
      voltageL1
      voltageL2
      voltageL3
      frequency
      timestamp
    }
  }
`;

// Query for power quality metrics
export const POWER_QUALITY_QUERY = `
  query PowerQuality($limit: Int, $sensorId: String, $hours: Int) {
    powerQuality(options: { limit: $limit, sensorId: $sensorId, timeRange: { hours: $hours } }) {
      id
      sensorId
      location
      thdVoltage
      thdCurrent
      powerFactor
      voltageImbalance
      flickerSeverity
      timestamp
    }
  }
`;

// Query for fault events
export const FAULT_EVENTS_QUERY = `
  query FaultEvents($limit: Int, $severity: String, $hours: Int) {
    faultEvents(options: { limit: $limit, severity: $severity, timeRange: { hours: $hours } }) {
      id
      eventId
      severity
      eventType
      location
      timestamp
      durationMs
      resolved
      resolvedAt
    }
  }
`;

// Query for sensor statistics
export const SENSOR_STATS_QUERY = `
  query SensorStats {
    sensorStats {
      totalSensors
      activeSensors
      faultCount24h
      violationCount24h
      avgVoltage
      minVoltage
      maxVoltage
    }
  }
`;

// Mutation for ingesting voltage reading
export const INGEST_VOLTAGE_MUTATION = `
  mutation IngestVoltageReading(
    $sensorId: String!
    $location: String!
    $voltageL1: Float!
    $voltageL2: Float!
    $voltageL3: Float!
    $frequency: Float!
    $timestamp: DateTime!
  ) {
    ingestVoltageReading(
      reading: {
        sensorId: $sensorId
        location: $location
        voltageL1: $voltageL1
        voltageL2: $voltageL2
        voltageL3: $voltageL3
        frequency: $frequency
        timestamp: $timestamp
      }
    ) {
      success
      message
      id
    }
  }
`;

// Mutation for ingesting power quality data
export const INGEST_POWER_QUALITY_MUTATION = `
  mutation IngestPowerQuality(
    $sensorId: String!
    $location: String!
    $thdVoltage: Float!
    $thdCurrent: Float!
    $powerFactor: Float!
    $voltageImbalance: Float!
    $flickerSeverity: Float!
    $timestamp: DateTime!
  ) {
    ingestPowerQuality(
      data: {
        sensorId: $sensorId
        location: $location
        thdVoltage: $thdVoltage
        thdCurrent: $thdCurrent
        powerFactor: $powerFactor
        voltageImbalance: $voltageImbalance
        flickerSeverity: $flickerSeverity
        timestamp: $timestamp
      }
    ) {
      success
      message
      id
    }
  }
`;

// Mutation for creating fault event
export const CREATE_FAULT_EVENT_MUTATION = `
  mutation CreateFaultEvent(
    $eventId: String!
    $severity: String!
    $eventType: String!
    $location: String!
    $timestamp: DateTime!
    $durationMs: Int!
  ) {
    createFaultEvent(
      event: {
        eventId: $eventId
        severity: $severity
        eventType: $eventType
        location: $location
        timestamp: $timestamp
        durationMs: $durationMs
      }
    ) {
      success
      message
      id
    }
  }
`;
