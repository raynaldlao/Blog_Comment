import { describe, it, expect, vi, afterEach } from 'vitest';
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import useCodeBlockGapClick from '../hooks/useCodeBlockGapClick';

function TestHarness({ editorRef }) {
  useCodeBlockGapClick(editorRef);
  return null;
}

let roots = [];

function render(ui) {
  const container = document.createElement('div');
  container.id = 'test-root';
  const root = createRoot(container);
  roots.push(root);
  act(() => { root.render(ui); });
  document.body.appendChild(container);
  return container;
}

afterEach(() => {
  roots.forEach((r) => { r.unmount(); });
  roots = [];
  vi.useRealTimers();
  document.body.innerHTML = '';
  vi.restoreAllMocks();
});

function addBlockToDOM(props = {}) {
  const {
    blockId = 'block',
    top = 0,
    bottom = 100,
    left = 0,
    right = 100,
    width = 100,
    height = 100,
    contentType = null,
    useMediaWrapper = false,
  } = props;

  const inner = document.createElement('div');
  if (useMediaWrapper) {
    inner.className = 'bn-visual-media-wrapper';
  } else {
    inner.className = 'bn-block-content';
    if (contentType) inner.setAttribute('data-content-type', contentType);
  }

  const blockOuter = document.createElement('div');
  blockOuter.className = 'bn-block-outer';
  blockOuter.setAttribute('data-id', blockId);

  vi.spyOn(blockOuter, 'getBoundingClientRect').mockReturnValue({
    top, bottom, left, right,
    width, height,
    x: left, y: top,
    toJSON() {},
  });

  blockOuter.appendChild(inner);

  const container = document.getElementById('test-root') || document.body;
  container.appendChild(blockOuter);
  return { inner, blockOuter };
}

describe('useCodeBlockGapClick', () => {
  it('inserts paragraph when clicking below code block', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-block-1' }]);
    const focus = vi.fn();
    const documentBlocks = [{ id: 'block-1', type: 'codeBlock' }];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'block-1', bottom: 100, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 108,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    vi.advanceTimersByTime(0);

    expect(insertBlocks).toHaveBeenCalledWith(
      [{ type: 'paragraph' }],
      'block-1',
      'after',
      false,
    );

    vi.useRealTimers();
  });

  it('focuses editor when paragraph already exists below code block', () => {
    const insertBlocks = vi.fn();
    const focus = vi.fn();
    const setTextCursorPosition = vi.fn();
    const documentBlocks = [
      { id: 'code-1', type: 'codeBlock' },
      { id: 'p-1', type: 'paragraph' },
    ];
    const editorRef = {
      current: { document: documentBlocks, insertBlocks, focus, setTextCursorPosition },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'code-1', bottom: 100, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 108,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    expect(insertBlocks).not.toHaveBeenCalled();
    expect(setTextCursorPosition).not.toHaveBeenCalled();
    expect(focus).not.toHaveBeenCalled();
  });

  it('does not insert when clicking far below code block', () => {
    const insertBlocks = vi.fn();
    const editorRef = { current: { insertBlocks, focus: vi.fn(), setTextCursorPosition: vi.fn(), document: [] } };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'block-2', bottom: 100, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 200,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    expect(insertBlocks).not.toHaveBeenCalled();
  });

  it('inserts paragraph before when clicking above code block', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-block-6' }]);
    const focus = vi.fn();
    const documentBlocks = [{ id: 'block-6', type: 'codeBlock' }];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'block-6', top: 100, bottom: 200, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 92,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    vi.advanceTimersByTime(0);

    expect(insertBlocks).toHaveBeenCalledWith(
      [{ type: 'paragraph' }],
      'block-6',
      'before',
      false,
    );

    vi.useRealTimers();
  });

  it('skips insertion above code block when adjacent paragraph is empty', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn();
    const focus = vi.fn();
    const documentBlocks = [
      { id: 'p-7', type: 'paragraph' },
      { id: 'code-7', type: 'codeBlock' },
    ];
    const editorRef = {
      current: { document: documentBlocks, insertBlocks, focus },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'code-7', top: 100, bottom: 200, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 92,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);
    vi.advanceTimersByTime(0);

    expect(insertBlocks).not.toHaveBeenCalled();
    expect(focus).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('skips insertion on repeated click above empty paragraph', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn();
    const focus = vi.fn();
    const documentBlocks = [
      { id: 'p-7', type: 'paragraph' },
      { id: 'code-7', type: 'codeBlock' },
    ];
    const editorRef = {
      current: { document: documentBlocks, insertBlocks, focus },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'code-7', top: 100, bottom: 200, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 92,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);
    expect(insertBlocks).not.toHaveBeenCalled();

    container.dispatchEvent(event);
    expect(insertBlocks).not.toHaveBeenCalled();
    expect(focus).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('only inserts once for gap between two code blocks via reverse key', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-p' }]);
    const focus = vi.fn();
    const documentBlocks = [
      { id: 'code-a', type: 'codeBlock' },
      { id: 'code-b', type: 'codeBlock' },
    ];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'code-a', top: 0, bottom: 100, contentType: 'codeBlock' });
    addBlockToDOM({ blockId: 'code-b', top: 124, bottom: 224, contentType: 'codeBlock' });

    const clickGap = (y) => {
      const event = new MouseEvent('mousedown', {
        clientY: y, bubbles: true, cancelable: true,
      });
      container.dispatchEvent(event);
      vi.advanceTimersByTime(0);
    };

    clickGap(108);
    expect(insertBlocks).toHaveBeenCalledTimes(1);

    clickGap(116);
    expect(insertBlocks).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('inserts paragraph when clicking below video block', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-vid-p' }]);
    const focus = vi.fn();
    const documentBlocks = [{ id: 'vid-1', type: 'video' }];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'vid-1', bottom: 100, useMediaWrapper: true });

    const event = new MouseEvent('mousedown', {
      clientY: 108,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    vi.advanceTimersByTime(0);

    expect(insertBlocks).toHaveBeenCalledWith(
      [{ type: 'paragraph' }],
      'vid-1',
      'after',
      false,
    );

    vi.useRealTimers();
  });

  it('inserts paragraph when clicking above video block', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-vid-p2' }]);
    const focus = vi.fn();
    const documentBlocks = [{ id: 'vid-2', type: 'video' }];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'vid-2', top: 100, bottom: 200, useMediaWrapper: true });

    const event = new MouseEvent('mousedown', {
      clientY: 92,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    vi.advanceTimersByTime(0);

    expect(insertBlocks).toHaveBeenCalledWith(
      [{ type: 'paragraph' }],
      'vid-2',
      'before',
      false,
    );

    vi.useRealTimers();
  });

  it('skips insertion above video block when adjacent paragraph is empty', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn();
    const focus = vi.fn();
    const documentBlocks = [
      { id: 'p-before-vid', type: 'paragraph' },
      { id: 'vid-3', type: 'video' },
    ];
    const editorRef = {
      current: { document: documentBlocks, insertBlocks, focus },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'vid-3', top: 100, bottom: 200, useMediaWrapper: true });

    const event = new MouseEvent('mousedown', {
      clientY: 92,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);
    vi.advanceTimersByTime(0);

    expect(insertBlocks).not.toHaveBeenCalled();
    expect(focus).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('does not insert when clicking far below video block', () => {
    const insertBlocks = vi.fn();
    const editorRef = { current: { insertBlocks, focus: vi.fn(), setTextCursorPosition: vi.fn(), document: [] } };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'vid-4', bottom: 100, useMediaWrapper: true });

    const event = new MouseEvent('mousedown', {
      clientY: 200,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    expect(insertBlocks).not.toHaveBeenCalled();
  });

  it('inserts paragraph when clicking below image block', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-img-p' }]);
    const focus = vi.fn();
    const documentBlocks = [{ id: 'img-1', type: 'image' }];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'img-1', bottom: 100, contentType: 'image' });

    const event = new MouseEvent('mousedown', {
      clientY: 108,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    vi.advanceTimersByTime(0);

    expect(insertBlocks).toHaveBeenCalledWith(
      [{ type: 'paragraph' }],
      'img-1',
      'after',
      false,
    );

    vi.useRealTimers();
  });

  it('collapses DOM selection on Backspace when selection is non-collapsed on empty paragraph', () => {
    const tiptapState = {
      selection: {
        $from: {
          parent: { type: { name: 'paragraph' }, content: { size: 0 } },
        },
      },
    };
    const editorRef = {
      current: {
        _tiptapEditor: { state: tiptapState },
        getTextCursorPosition: () => ({ block: { id: 'p-1', type: 'paragraph', content: [] } }),
      },
    };

    render(React.createElement(TestHarness, { editorRef }));

    const p = document.createElement('p');
    p.innerHTML = '<br class="ProseMirror-trailingBreak">';
    document.body.appendChild(p);

    const sel = window.getSelection();
    const range = document.createRange();
    range.setStart(p, 0);
    range.setEnd(p, 1);
    sel.removeAllRanges();
    sel.addRange(range);
    expect(range.collapsed).toBe(false);

    const event = new KeyboardEvent('keydown', {
      key: 'Backspace', cancelable: true, bubbles: true,
    });
    const preventSpy = vi.spyOn(event, 'preventDefault');
    const stopSpy = vi.spyOn(event, 'stopPropagation');
    document.dispatchEvent(event);

    expect(preventSpy).toHaveBeenCalled();
    expect(stopSpy).toHaveBeenCalled();

    const selAfter = window.getSelection();
    expect(selAfter.rangeCount).toBe(1);
    expect(selAfter.getRangeAt(0).collapsed).toBe(true);
  });

  it('does not intercept Backspace when DOM selection is already collapsed', () => {
    const tiptapState = {
      selection: {
        $from: { depth: 3, parent: { type: { name: 'paragraph' }, content: { size: 0 } } },
      },
    };
    const editorRef = {
      current: {
        _tiptapEditor: { state: tiptapState },
        getTextCursorPosition: () => ({ block: { id: 'p-1', type: 'paragraph', content: [] } }),
      },
    };

    render(React.createElement(TestHarness, { editorRef }));

    const p = document.createElement('p');
    document.body.appendChild(p);

    const sel = window.getSelection();
    const range = document.createRange();
    range.setStart(p, 0);
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);

    const event = new KeyboardEvent('keydown', {
      key: 'Backspace', cancelable: true, bubbles: true,
    });
    const preventSpy = vi.spyOn(event, 'preventDefault');
    document.dispatchEvent(event);

    expect(preventSpy).not.toHaveBeenCalled();
  });

  it('does not insert when clicking on code block content', () => {
    const insertBlocks = vi.fn();
    const editorRef = { current: { insertBlocks, focus: vi.fn(), setTextCursorPosition: vi.fn(), document: [] } };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'block-3', bottom: 100, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 50,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    expect(insertBlocks).not.toHaveBeenCalled();
  });

  it('ignores clicks when editor is null', () => {
    const insertBlocks = vi.fn();
    const editorRef = { current: null };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'block-4', bottom: 100, contentType: 'codeBlock' });

    const event = new MouseEvent('mousedown', {
      clientY: 108,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    expect(insertBlocks).not.toHaveBeenCalled();
  });

  it('re-inserts paragraph after 300ms debounce window expires', () => {
    vi.useFakeTimers();
    const insertBlocks = vi.fn(() => [{ id: 'new-p' }]);
    const focus = vi.fn();
    const documentBlocks = [{ id: 'block-r', type: 'codeBlock' }];
    const editorRef = {
      current: { insertBlocks, focus, document: documentBlocks },
    };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addBlockToDOM({ blockId: 'block-r', bottom: 100, contentType: 'codeBlock' });

    const click = (y) => {
      const event = new MouseEvent('mousedown', {
        clientY: y, bubbles: true, cancelable: true,
      });
      container.dispatchEvent(event);
      vi.advanceTimersByTime(0);
    };

    click(108);
    expect(insertBlocks).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(301);

    click(108);
    expect(insertBlocks).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it('handles missing block ID gracefully', () => {
    const insertBlocks = vi.fn(() => [{ id: 'new-block-5' }]);
    const editorRef = { current: { insertBlocks, focus: vi.fn(), setTextCursorPosition: vi.fn(), document: [] } };

    const container = render(React.createElement(TestHarness, { editorRef }));

    const codeBlock = document.createElement('div');
    codeBlock.className = 'bn-block-content';
    codeBlock.setAttribute('data-content-type', 'codeBlock');
    const blockOuter = document.createElement('div');
    blockOuter.className = 'bn-block-outer';
    vi.spyOn(blockOuter, 'getBoundingClientRect').mockReturnValue({
      top: 0, bottom: 100, left: 0, right: 100,
      width: 100, height: 100, x: 0, y: 0,
      toJSON: () => {},
    });
    blockOuter.appendChild(codeBlock);
    container.appendChild(blockOuter);

    const event = new MouseEvent('mousedown', {
      clientY: 108,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(event);

    expect(insertBlocks).not.toHaveBeenCalled();
  });
});
