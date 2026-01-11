import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Archives from './Archives';

describe('Archives', () => {
  const mockToken = 'mock-jwt-token';

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders archives heading', () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [] }),
    });

    render(<Archives token={mockToken} />);
    expect(screen.getByText('📁 Data Archives')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    global.fetch.mockImplementationOnce(
      () => new Promise(() => {}) // Never resolves
    );

    render(<Archives token={mockToken} />);
    expect(screen.getByText('Refreshing…')).toBeInTheDocument();
  });

  it('fetches and displays archive files', async () => {
    const mockFiles = [
      {
        key: 'exports/voltage_2026-01-11.json',
        size: 1024,
        last_modified: '2026-01-11T10:30:00Z',
      },
      {
        key: 'exports/faults_2026-01-10.csv',
        size: 2048,
        last_modified: '2026-01-10T15:45:00Z',
      },
    ];

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: mockFiles }),
    });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('exports/voltage_2026-01-11.json')).toBeInTheDocument();
    });

    expect(screen.getByText('exports/faults_2026-01-10.csv')).toBeInTheDocument();
    expect(screen.getByText('1024')).toBeInTheDocument();
    expect(screen.getByText('2048')).toBeInTheDocument();
  });

  it('displays message when no archives exist', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [] }),
    });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('No exports yet')).toBeInTheDocument();
    });
  });

  it('displays error message on fetch failure', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load archives/i)).toBeInTheDocument();
    });
  });

  it('handles network error gracefully', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load archives/i)).toBeInTheDocument();
    });
  });

  it('formats file sizes correctly', async () => {
    const mockFiles = [
      { key: 'file1.json', size: 500, last_modified: '2026-01-11T10:00:00Z' },
      { key: 'file2.json', size: 1536, last_modified: '2026-01-11T10:00:00Z' },
      { key: 'file3.json', size: 1048576, last_modified: '2026-01-11T10:00:00Z' },
      { key: 'file4.json', size: 1073741824, last_modified: '2026-01-11T10:00:00Z' },
    ];

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: mockFiles }),
    });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('500')).toBeInTheDocument();
      expect(screen.getByText('1536')).toBeInTheDocument();
      expect(screen.getByText('1048576')).toBeInTheDocument();
      expect(screen.getByText('1073741824')).toBeInTheDocument();
    });
  });

  it('handles download button click', async () => {
    const mockFiles = [
      {
        key: 'exports/voltage_2026-01-11.json',
        size: 1024,
        modified: '2026-01-11T10:30:00Z',
      },
    ];

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: mockFiles }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success', url: 'https://s3.mock.url/signed' }),
      });

    // Mock window.open
    const mockOpen = vi.fn();
    window.open = mockOpen;

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('exports/voltage_2026-01-11.json')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/export/exports/voltage_2026-01-11.json',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      );
      expect(mockOpen).toHaveBeenCalledWith('https://s3.mock.url/signed', '_blank');
    });
  });

  it('displays error on download failure', async () => {
    const mockFiles = [
      {
        key: 'exports/test.json',
        size: 1024,
        modified: '2026-01-11T10:30:00Z',
      },
    ];

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: mockFiles }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Not found' }),
      });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('exports/test.json')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByText(/Download failed/i)).toBeInTheDocument();
    });
  });

  it('displays full key path for nested files', async () => {
    const mockFiles = [
      {
        key: 'exports/subdir/deep/file.json',
        size: 1024,
        modified: '2026-01-11T10:30:00Z',
      },
    ];

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: mockFiles }),
    });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('exports/subdir/deep/file.json')).toBeInTheDocument();
    });
  });

  it('fetches archives on component mount', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [] }),
    });

    render(<Archives token={mockToken} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/export/list',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      );
    });
  });
});
