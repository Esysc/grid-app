import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock fetch globally
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock EventSource
global.EventSource = vi.fn(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  close: vi.fn(),
}));

// Provide a canvas getContext stub ONLY if not usable (e.g., when `canvas` isn't installed)
if (typeof window !== 'undefined' && window.HTMLCanvasElement) {
  let needsMock = false;
  try {
    const c = document.createElement('canvas');
    const ctx = c.getContext && c.getContext('2d');
    if (!ctx) needsMock = true;
  } catch (e) {
    needsMock = true;
  }
  if (needsMock) {
    Object.defineProperty(window.HTMLCanvasElement.prototype, 'getContext', {
      configurable: true,
      writable: true,
      value: vi.fn(() => ({
        // minimal 2D context stub used by libraries for measurement
        fillRect: () => {},
        clearRect: () => {},
        getImageData: () => ({ data: [] }),
        putImageData: () => {},
        createImageData: () => [],
        setTransform: () => {},
        drawImage: () => {},
        save: () => {},
        fillText: () => {},
        restore: () => {},
        beginPath: () => {},
        moveTo: () => {},
        lineTo: () => {},
        closePath: () => {},
        stroke: () => {},
        translate: () => {},
        scale: () => {},
        rotate: () => {},
        arc: () => {},
        fill: () => {},
        measureText: () => ({ width: 0 }),
        transform: () => {},
        rect: () => {},
        clip: () => {},
      })),
    });
  }
}

// Mock alert to avoid jsdom not-implemented warnings
if (typeof window !== 'undefined') {
  window.alert = vi.fn();
}
