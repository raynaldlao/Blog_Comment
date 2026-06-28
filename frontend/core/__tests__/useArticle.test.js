import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import useArticle from '../hooks/useArticle';

function TestHarness({ articleId }) {
  const state = useArticle(articleId);
  return React.createElement('div', {
    'data-loaded': String(state.loaded),
    'data-content': state.contentStr,
    'data-error': state.error,
    'data-title': state.title,
  });
}

function render(ui) {
  const container = document.createElement('div');
  const root = createRoot(container);
  act(() => { root.render(ui); });
  return container;
}

beforeEach(() => {
  globalThis.fetch = vi.fn();
});

afterEach(() => {
  document.body.innerHTML = '';
  delete globalThis.fetch;
});

function flushMicrotasks() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe('useArticle', () => {
  it('returns loaded=true immediately when articleId is null', () => {
    const container = render(React.createElement(TestHarness, { articleId: null }));
    expect(container.querySelector('[data-loaded="true"]')).not.toBeNull();
  });

  it('returns loaded=true immediately when articleId is undefined', () => {
    const container = render(React.createElement(TestHarness, {}));
    expect(container.querySelector('[data-loaded="true"]')?.dataset.loaded).toBe('true');
  });

  it('fetches article on mount and returns content', async () => {
    globalThis.fetch.mockResolvedValue({
      json: () => Promise.resolve({ title: 'My Title', content: '{"type":"doc"}' }),
    });

    const container = render(React.createElement(TestHarness, { articleId: '42' }));
    expect(container.querySelector('[data-loaded="false"]')).not.toBeNull();

    await act(async () => {
      await flushMicrotasks();
    });

    expect(container.querySelector('[data-loaded="true"]')).not.toBeNull();
    expect(container.querySelector('[data-title="My Title"]')).not.toBeNull();
    expect(container.querySelector('[data-content]')?.dataset.content).toBe('{"type":"doc"}');
  });

  it('sets error when fetch fails', async () => {
    globalThis.fetch.mockRejectedValue(new Error('Network error'));

    const container = render(React.createElement(TestHarness, { articleId: '42' }));

    await act(async () => {
      await flushMicrotasks();
    });

    expect(container.querySelector('[data-loaded="true"]')).not.toBeNull();
    expect(container.querySelector('[data-error]')?.dataset.error).toBeTruthy();
  });

  it('sets error when fetch returns non-JSON', async () => {
    globalThis.fetch.mockResolvedValue({
      json: () => Promise.reject(new Error('Invalid JSON')),
    });

    const container = render(React.createElement(TestHarness, { articleId: '42' }));

    await act(async () => {
      await flushMicrotasks();
    });

    expect(container.querySelector('[data-loaded="true"]')).not.toBeNull();
    expect(container.querySelector('[data-error]')?.dataset.error).toBeTruthy();
  });
});
