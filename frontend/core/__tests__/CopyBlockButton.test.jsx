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
  var container = document.createElement('div');
  var root = createRoot(container);
  act(function () { root.render(ui); });
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

describe('CopyBlockButton', function () {
  var mockWrite;
  var lastItems;

  beforeEach(function () {
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

  afterEach(function () {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  function setup(blockData) {
    var editor = {
      getSelection: vi.fn().mockReturnValue({ blocks: [blockData] }),
      getTextCursorPosition: vi.fn(),
    };
    useBlockNoteEditor.mockReturnValue(editor);
    useComponentsContext.mockReturnValue({
      FormattingToolbar: { Button: mockButton },
    });
    return editor;
  }

  describe('null guards', function () {
    it('returns null when editor is null', function () {
      useBlockNoteEditor.mockReturnValue(null);
      useComponentsContext.mockReturnValue({ FormattingToolbar: { Button: mockButton } });
      var container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });

    it('returns null when Components is null', function () {
      setup(makeBlock());
      useComponentsContext.mockReturnValue(null);
      var container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });

    it('returns null when block is null', function () {
      setup(null);
      var container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });

    it('handles selection error gracefully', function () {
      var editor = { getSelection: vi.fn().mockImplementation(function () { throw new Error('fail'); }) };
      useBlockNoteEditor.mockReturnValue(editor);
      useComponentsContext.mockReturnValue({ FormattingToolbar: { Button: mockButton } });
      var container = render(React.createElement(CopyBlockButton));
      expect(container.innerHTML).toBe('');
    });
  });

  describe('tooltip', function () {
    it('shows "Copy" for image block', function () {
      setup(makeBlock({ type: 'image' }));
      var container = render(React.createElement(CopyBlockButton));
      var btn = container.querySelector('[data-testid="copy-btn"]');
      expect(btn.dataset.tooltip).toBe('Copy');
    });

    it('shows "Copy" for video block', function () {
      setup(makeBlock({ type: 'video' }));
      var container = render(React.createElement(CopyBlockButton));
      var btn = container.querySelector('[data-testid="copy-btn"]');
      expect(btn.dataset.tooltip).toBe('Copy');
    });

    it('shows "Copy Block" for other block types', function () {
      setup(makeBlock({ type: 'codeBlock' }));
      var container = render(React.createElement(CopyBlockButton));
      var btn = container.querySelector('[data-testid="copy-btn"]');
      expect(btn.dataset.tooltip).toBe('Copy Block');
    });
  });

  describe('plainText per block type', function () {
    it('image upload → writes alt text', async function () {
      setup(makeBlock({ type: 'image', props: { url: '/uploads/foo.jpg', alt: 'my photo' } }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var text = await lastItems['text/plain'].text();
      expect(text).toBe('my photo');
    });

    it('image upload without alt → writes name', async function () {
      setup(makeBlock({ type: 'image', props: { url: '/uploads/foo.jpg', name: 'Foo' } }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var text = await lastItems['text/plain'].text();
      expect(text).toBe('Foo');
    });

    it('image external URL → writes URL (ignores alt)', async function () {
      setup(makeBlock({ type: 'image', props: { url: 'https://example.com/img.jpg', alt: 'alt text' } }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var text = await lastItems['text/plain'].text();
      expect(text).toBe('https://example.com/img.jpg');
    });

    it('video → writes URL', async function () {
      setup(makeBlock({ type: 'video', props: { url: 'https://youtube.com/watch?v=abc' } }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var text = await lastItems['text/plain'].text();
      expect(text).toBe('https://youtube.com/watch?v=abc');
    });

    it('other block (code) → writes URL', async function () {
      setup(makeBlock({ type: 'codeBlock', props: { url: '' } }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var text = await lastItems['text/plain'].text();
      expect(text).toBe('');
    });
  });

  describe('ClipboardItem', function () {
    it('contains text/plain and text/html entries', function () {
      setup(makeBlock({ type: 'image', props: { url: '/uploads/foo.jpg', alt: 'img' } }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      expect(lastItems).toHaveProperty('text/plain');
      expect(lastItems).toHaveProperty('text/html');
      expect(Object.keys(lastItems).length).toBe(2);
    });

    it('has correct text/html marker', async function () {
      setup(makeBlock({ type: 'paragraph', props: { url: '' }, content: 'hello' }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var html = await lastItems['text/html'].text();
      expect(html).toContain('blocknote-block');
      expect(html).toContain('paragraph');
    });
  });

  describe('toast', function () {
    it('shows toast on click', function () {
      setup(makeBlock({ type: 'paragraph' }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      var toast = document.querySelector('.toast');
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe('Copied to clipboard');
    });

    it('removes old toast before creating new one', function () {
      setup(makeBlock({ type: 'paragraph' }));
      var container = render(React.createElement(CopyBlockButton));
      var btn = container.querySelector('[data-testid="copy-btn"]');
      act(function () { btn.click(); });
      act(function () { btn.click(); });
      var toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBe(1);
    });

    it('removes toast after 2800ms', function () {
      setup(makeBlock({ type: 'paragraph' }));
      var container = render(React.createElement(CopyBlockButton));
      act(function () { container.querySelector('[data-testid="copy-btn"]').click(); });
      expect(document.querySelector('.toast')).not.toBeNull();
      vi.advanceTimersByTime(2800);
      expect(document.querySelector('.toast')).toBeNull();
    });
  });
});
