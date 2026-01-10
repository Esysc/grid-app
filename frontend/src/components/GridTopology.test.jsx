import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import GridTopology from '../components/GridTopology';

describe('GridTopology Component', () => {
  test('renders grid topology heading', () => {
    render(<GridTopology />);
    const heading = screen.getByRole('heading', { name: /🔌 Grid Topology Visualization/i });
    expect(heading).toBeInTheDocument();
  });

  test('renders canvas element', () => {
    render(<GridTopology />);
    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toBeInTheDocument();
  });

  test('renders description text', () => {
    render(<GridTopology />);
    expect(
      screen.getByText(/Interactive visualization of the power grid network/i)
    ).toBeInTheDocument();
  });
});
