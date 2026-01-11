import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock the fetch API
globalThis.fetch = jest.fn();

// Mock the matchMedia API
globalThis.matchMedia = globalThis.matchMedia || function () {
  return {
    matches: false,
    addListener: function () { },
    removeListener: function () { }
  };
};

describe('App Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders app header', () => {
    render(<App />);
    const header = screen.getByRole('heading', { name: /⚡ Grid Monitor/i });
    expect(header).toBeInTheDocument();
  });

  test('renders main sections', () => {
    render(<App />);
    expect(screen.getByText(/Grid Monitoring & Analytics Platform/i)).toBeInTheDocument();
  });

  test('renders footer', () => {
    render(<App />);
    expect(screen.getByText(/Grid Monitor - Real-time Grid Analytics/i)).toBeInTheDocument();
  });
});
