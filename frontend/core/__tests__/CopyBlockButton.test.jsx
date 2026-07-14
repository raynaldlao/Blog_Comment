import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import CopyBlockButton from '../components/CopyBlockButton';

vi.mock('@blocknote/react', () => ({
  useBlockNoteEditor: vi.fn(),
  useComponentsContext: vi.fn(),
}));

import { useBlockNoteEditor, useComponentsContext } from '@blocknote/react';

function render(ui) {
  const container = document.createElement('div');
  const root = createRoot(container);
  act(() => { root.render(ui); });
  return container;
}

function makeBlock(overrides) {
  return { type: 'paragraph', props: {}, content: '', ...overrides };
}

function mockButton(props) {
  return React.createElement('button', {
    'data-testid': 'copy-btn',
    'data-tooltip': props.mainTooltip,
    onClick: props.onClick,
  });
}

describe('CopyBlockButton', () => {
  let mockWrite;
  let lastItems;

  beforeEach(() => {
    vi.useFakeTimers();
    mockWrite = vi.fn().mockResolvedValue(undefined);
    lastItems = null;
    vi.stubGlobal('navigator', {
      clipboard: { write: mockWrite },
    });
    vi.stubGlobal('ClipboardItem', vi.fn(function (items) {
      lastItems = items;
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  function setup(blockData) {
    const editor = {
      getSelection: vi.fn().mockReturnValue({ blocks: [blockData] }),
      getTextCursorPosition: vi.fn(),
    };
    useBlockNoteEditor.mockReturnValue(editor);
    useComponentsContext.mockReturnValue({
      FormattingToolbar: { Button: mockButton },
    });
    return editor;
  }

  describe('null guards', () => {
    it('returns null when editor is null', () => {
      useBlockNoteEditor.mockReturnValue(null);
      useComponentsContext.mockReturnValue({ FormattingToolbar: { Button: mockButton } });
      const container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });

    it('returns null when Components is null', () => {
      setup(makeBlock());
      useComponentsContext.mockReturnValue(null);
      const container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });

    it('returns null when block is null', () => {
      setup(null);
      const container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });

    it('handles selection error gracefully', () => {
      const editor = { getSelection: vi.fn().mockImplementation(() => { throw new Error('fail'); }) };
      useBlockNoteEditor.mockReturnValue(editor);
      useComponentsContext.mockReturnValue({ FormattingToolbar: { Button: mockButton } });
      const container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });
  });

  describe('tooltip', () => {
    it('shows "Copy" for image block', () => {
      setup(makeBlock({ type: 'image' }));
      const container = render(React.createElement(CopyBlockButton));
      const btn = container.querySelector('[data-testid="copy-btn"]');
      expect(btn.dataset.tooltip).toBe('Copy');
    });

    it('shows "Copy" for video block', () => {
      setup(makeBlock({ type: 'video' }));
      const container = render(React.createElement(CopyBlockButton));
      const btn = container.querySelector('[data-testid="copy-btn"]');
      expect(btn.dataset.tooltip).toBe('Copy');
    });

    it('shows "Copy Block" for other block types', () => {
      setup(makeBlock({ type: 'codeBlock' }));
      const container = render(React.createElement(CopyBlockButton));
      const btn = container.querySelector('[data-testid="copy-btn"]');
      expect(btn.dataset.tooltip).toBe('Copy Block');
    });
  });

  describe('plainText per block type', () => {
    it('image upload → writes alt text', async () => {
      setup(makeBlock({ type: 'image', props: { url: '/uploads/foo.jpg', alt: 'my photo' } }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const text = await lastItems['text/plain'].text();
      expect(text).toBe('my photo');
    });

    it('image upload without alt → writes name', async () => {
      setup(makeBlock({ type: 'image', props: { url: '/uploads/foo.jpg', name: 'Foo' } }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const text = await lastItems['text/plain'].text();
      expect(text).toBe('Foo');
    });

    it('image external URL → writes URL (ignores alt)', async () => {
      setup(makeBlock({ type: 'image', props: { url: 'https://example.com/img.jpg', alt: 'alt text' } }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const text = await lastItems['text/plain'].text();
      expect(text).toBe('https://example.com/img.jpg');
    });

    it('video → writes URL', async () => {
      setup(makeBlock({ type: 'video', props: { url: 'https://youtube.com/watch?v=abc' } }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const text = await lastItems['text/plain'].text();
      expect(text).toBe('https://youtube.com/watch?v=abc');
    });

    it('other block (code) → writes URL', async () => {
      setup(makeBlock({ type: 'codeBlock', props: { url: '' } }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const text = await lastItems['text/plain'].text();
      expect(text).toBe('');
    });
  });

  describe('ClipboardItem', () => {
    it('contains text/plain and text/html entries', () => {
      setup(makeBlock({ type: 'image', props: { url: '/uploads/foo.jpg', alt: 'img' } }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      expect(lastItems).toHaveProperty('text/plain');
      expect(lastItems).toHaveProperty('text/html');
      expect(Object.keys(lastItems).length).toBe(2);
    });

    it('has correct text/html marker', async () => {
      setup(makeBlock({ type: 'paragraph', props: { url: '' }, content: 'hello' }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const html = await lastItems['text/html'].text();
      expect(html).toContain('blocknote-block');
      expect(html).toContain('paragraph');
    });
  });

  describe('toast', () => {
    it('shows toast on click', () => {
      setup(makeBlock({ type: 'paragraph' }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      const toast = document.querySelector('.toast');
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe('Copied to clipboard');
    });

    it('removes old toast before creating new one', () => {
      setup(makeBlock({ type: 'paragraph' }));
      const container = render(React.createElement(CopyBlockButton));
      const btn = container.querySelector('[data-testid="copy-btn"]');
      act(() => { btn.click(); });
      act(() => { btn.click(); });
      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBe(1);
    });

    it('removes toast after 2800ms', () => {
      setup(makeBlock({ type: 'paragraph' }));
      const container = render(React.createElement(CopyBlockButton));
      act(() => { container.querySelector('[data-testid="copy-btn"]').click(); });
      expect(document.querySelector('.toast')).not.toBeNull();
      vi.advanceTimersByTime(2800);
      expect(document.querySelector('.toast')).toBeNull();
    });
  });
});
