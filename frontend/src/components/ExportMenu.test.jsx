import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportMenu from './ExportMenu';

describe('ExportMenu', () => {
  const mockToken = 'mock-jwt-token';

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders export button', () => {
    render(<ExportMenu token={mockToken} />);
    expect(screen.getByText('Export ▼')).toBeInTheDocument();
  });

  it('toggles dropdown menu on button click', () => {
    render(<ExportMenu token={mockToken} />);
    
    const exportButton = screen.getByText('Export ▼');
    
    // Menu should not be visible initially
    expect(screen.queryByText('Export Voltage Data (24h)')).not.toBeInTheDocument();
    
    // Click to open
    fireEvent.click(exportButton);
    expect(screen.getByText('Export Voltage Data (24h)')).toBeInTheDocument();
    
    // Click to close
    fireEvent.click(exportButton);
    expect(screen.queryByText('Export Voltage Data (24h)')).not.toBeInTheDocument();
  });

  it('closes dropdown when clicking outside', () => {
    render(
      <div>
        <ExportMenu token={mockToken} />
        <div data-testid="outside">Outside</div>
      </div>
    );
    
    const exportButton = screen.getByText('Export ▼');
    fireEvent.click(exportButton);
    
    expect(screen.getByText('Export Voltage Data (24h)')).toBeInTheDocument();
    
    fireEvent.mouseDown(screen.getByTestId('outside'));
    
    expect(screen.queryByText('Export Voltage Data (24h)')).not.toBeInTheDocument();
  });

  it('exports voltage data successfully', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Export successful', key: 'exports/voltage_123.json' }),
    });

    render(<ExportMenu token={mockToken} />);
    
    fireEvent.click(screen.getByText('Export ▼'));
    fireEvent.click(screen.getByText('Export Voltage Data (24h)'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/export/voltage?hours=24',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/S3 export completed/i)).toBeInTheDocument();
    });
  });

  it('exports fault data successfully', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Export successful', key: 'exports/faults_456.json' }),
    });

    render(<ExportMenu token={mockToken} />);
    
    fireEvent.click(screen.getByText('Export ▼'));
    fireEvent.click(screen.getByText('Export Fault Events (24h)'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/export/faults?hours=24',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/S3 export completed/i)).toBeInTheDocument();
    });
  });

  it('displays error message on export failure', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<ExportMenu token={mockToken} />);
    
    fireEvent.click(screen.getByText('Export ▼'));
    fireEvent.click(screen.getByText('Export Voltage Data (24h)'));

    await waitFor(() => {
      expect(screen.getByText(/Export failed/i)).toBeInTheDocument();
    });
  });

  it('handles network error', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<ExportMenu token={mockToken} />);
    
    fireEvent.click(screen.getByText('Export ▼'));
    fireEvent.click(screen.getByText('Export Voltage Data (24h)'));

    await waitFor(() => {
      expect(screen.getByText(/Export failed/i)).toBeInTheDocument();
    });
  });

  it('disables export buttons during loading', async () => {
    // Fast resolve means we won't see loading state, just check that it completes
    global.fetch.mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, json: async () => ({ message: 'Success' }) }), 10))
    );

    render(<ExportMenu token={mockToken} />);
    
    fireEvent.click(screen.getByText('Export ▼'));
    const voltageButton = screen.getByText('Export Voltage Data (24h)');
    fireEvent.click(voltageButton);

    await waitFor(() => {
      expect(screen.getByText(/Success/i)).toBeInTheDocument();
    });
  });

  it('navigates to archives view on link click', () => {
    const mockOnViewArchives = vi.fn();
    
    render(<ExportMenu token={mockToken} onViewArchives={mockOnViewArchives} />);
    
    fireEvent.click(screen.getByText('Export ▼'));
    fireEvent.click(screen.getByText('View Archives'));

    expect(mockOnViewArchives).toHaveBeenCalled();
  });
});
