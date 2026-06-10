import { describe, it, expect, vi, afterEach } from 'vitest';
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ErrorBoundary from '../components/ErrorBoundary';

function Broken() {
  throw new Error('test error');
}

function render(ui) {
  const container = document.createElement('div');
  const root = createRoot(container);
  act(() => { root.render(ui); });
  return container;
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const container = render(
      <ErrorBoundary>
        <div id="child">ok</div>
      </ErrorBoundary>,
    );
    expect(container.querySelector('#child')).not.toBeNull();
    expect(container.textContent).toContain('ok');
    spy.mockRestore();
  });

  it('catches error and shows fallback', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const container = render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    );
    expect(container.textContent).toContain('Something went wrong');
    spy.mockRestore();
  });

  it('calls console.error when error caught', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    );
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
