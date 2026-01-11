import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

describe('App', () => {
  let mockEventSource;
  
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    // Mock EventSource as a proper constructor
    mockEventSource = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      close: vi.fn(),
    };
    global.EventSource = vi.fn(function() {
      return mockEventSource;
    });
    
    // Mock fetch - default response with empty arrays to prevent data.map errors
    global.fetch = vi.fn();
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ 
        access_token: 'mock-token',
        total_sensors: 0, 
        total_faults_24h: 0, 
        violations: 0,
        faults: [],
        data: []
      }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders login form when not authenticated', () => {
    render(<App />);
    
    expect(screen.getByPlaceholderText('admin')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('secret')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('displays demo banner on login page', () => {
    render(<App />);
    
    expect(screen.getByText(/Demo: username:/i)).toBeInTheDocument();
    expect(screen.getByText(/admin/i)).toBeInTheDocument();
    expect(screen.getByText(/secret/i)).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    render(<App />);
    
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/auth/login', expect.any(Object));
    });
  });

  it('loads token from localStorage on mount', () => {
    localStorage.setItem('accessToken', 'stored-token');
    
    render(<App />);
    
    // Should skip login and show dashboard
    expect(screen.getByText(/⚡ Grid Monitor/i)).toBeInTheDocument();
  });

  it('displays dashboard view after successful login', async () => {
    render(<App />);
    
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Verify login form is no longer shown (authenticated state)
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /login/i })).not.toBeInTheDocument();
    }, { timeout: 2000 });
    
    // Verify EventSource was created
    expect(global.EventSource).toHaveBeenCalled();
  });

  it('switches to archives view when archives tab clicked', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Wait for authenticated state
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /login/i })).not.toBeInTheDocument();
    });
    
    const archivesTab = await screen.findByText('Archives', {}, { timeout: 2000 });
    fireEvent.click(archivesTab);
    
    await waitFor(() => {
      expect(screen.getByText('📁 Data Archives')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('highlights active tab', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Wait for authenticated state
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /login/i })).not.toBeInTheDocument();
    });
    
    // Wait for tabs to appear
    const dashboardTab = await screen.findByText('Dashboard', {}, { timeout: 2000 });
    const archivesTab = await screen.findByText('Archives', {}, { timeout: 2000 });
    
    // Dashboard should be active initially
    expect(dashboardTab.className).toContain('active');
    expect(archivesTab.className).not.toContain('active');
    
    // Switch to archives
    fireEvent.click(archivesTab);
    
    await waitFor(() => {
      expect(archivesTab.className).toContain('active');
      expect(dashboardTab.className).not.toContain('active');
    }, { timeout: 2000 });
  });

  it('handles logout', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Wait for logout button to appear
    const logoutButton = await screen.findByText('Logout', {}, { timeout: 2000 });
    fireEvent.click(logoutButton);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('admin')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('closes EventSource on logout', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Wait for EventSource to be created
    await waitFor(() => {
      expect(global.EventSource).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    const logoutButton = await screen.findByText('Logout', {}, { timeout: 2000 });
    fireEvent.click(logoutButton);
    
    await waitFor(() => {
      expect(mockEventSource.close).toHaveBeenCalled();
    }, { timeout: 1000 });
  });

  it('closes EventSource on component unmount', async () => {
    const { unmount } = render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Wait for EventSource to be created
    await waitFor(() => {
      expect(global.EventSource).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    unmount();
    
    expect(mockEventSource.close).toHaveBeenCalled();
  });

  it('renders ExportMenu in dashboard view', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByText('Export ▼')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('switches to archives view from ExportMenu', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    // Wait for Export button
    const exportButton = await screen.findByText('Export ▼', {}, { timeout: 2000 });
    fireEvent.click(exportButton);
    
    const viewArchivesButton = await screen.findByText('View Archives');
    fireEvent.click(viewArchivesButton);
    
    await waitFor(() => {
      expect(screen.getByText('📁 Data Archives')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('displays error in console on login failure', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    global.fetch.mockRejectedValueOnce(new Error('Login failed'));
    
    render(<App />);
    
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(usernameInput, { target: { value: 'wrong' } });
    fireEvent.change(passwordInput, { target: { value: 'wrong' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });
    
    consoleSpy.mockRestore();
  });

  it('creates EventSource with correct URL', async () => {
    render(<App />);
    
    // Login first
    const usernameInput = screen.getByPlaceholderText('admin');
    const passwordInput = screen.getByPlaceholderText('secret');
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.change(usernameInput, { target: { value: 'demo' } });
    fireEvent.change(passwordInput, { target: { value: 'demo' } });
    fireEvent.click(loginButton);
    
    await waitFor(() => {
      expect(global.EventSource).toHaveBeenCalledWith(
        expect.stringContaining('/api/stream')
      );
    }, { timeout: 2000 });
  });
});
