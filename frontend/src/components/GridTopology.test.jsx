import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import GridTopology from '../components/GridTopology';

describe('GridTopology Component', () => {
  const mockSensorStatus = [
    {
      sensor_id: 'VS-001',
      location: 'Substation A',
      is_operational: true,
      seconds_since_update: 5,
    },
  ];

  const mockVoltageData = [
    {
      sensor_id: 'VS-001',
      voltage_l1: 230.5,
      voltage_l2: 230.2,
      voltage_l3: 229.8,
      frequency: 50.0,
    },
  ];

  test('renders grid topology heading', () => {
    render(<GridTopology sensorStatus={mockSensorStatus} voltageData={mockVoltageData} />);
    const heading = screen.getByRole('heading', {
      name: /🔌 Grid Topology & Sensor Network/i,
    });
    expect(heading).toBeInTheDocument();
  });

  test('renders SVG element', () => {
    const { container } = render(
      <GridTopology sensorStatus={mockSensorStatus} voltageData={mockVoltageData} />
    );
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  test('renders topology description', () => {
    render(<GridTopology sensorStatus={mockSensorStatus} voltageData={mockVoltageData} />);
    const description = screen.getByText(/Interactive grid topology with real-time sensor data/i);
    expect(description).toBeInTheDocument();
  });

  test('renders with default empty sensor status', () => {
    const { container } = render(<GridTopology sensorStatus={[]} voltageData={[]} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});