import { describe, it, expect, vi, afterEach } from 'vitest';
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import useCodeBlockGapClick from '../hooks/useCodeBlockGapClick';

function TestHarness({ editorRef }) {
  useCodeBlockGapClick(editorRef);
  return null;
}

function render(ui) {
  const container = document.createElement('div');
  container.id = 'test-root';
  const root = createRoot(container);
  act(() => { root.render(ui); });
  document.body.appendChild(container);
  return container;
}

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
  vi.restoreAllMocks();
});

function addCodeBlockToDOM(props = {}) {
  const {
    blockId = 'block-1',
    top = 0,
    bottom = 100,
    left = 0,
    right = 100,
    width = 100,
    height = 100,
  } = props;

  const codeBlock = document.createElement('div');
  codeBlock.className = 'bn-block-content';
  codeBlock.setAttribute('data-content-type', 'codeBlock');

  const blockOuter = document.createElement('div');
  blockOuter.className = 'bn-block-outer';
  blockOuter.setAttribute('data-id', blockId);

  vi.spyOn(blockOuter, 'getBoundingClientRect').mockReturnValue({
    top, bottom, left, right, width, height,
    x: left, y: top,
    toJSON: () => {},
  });

  blockOuter.appendChild(codeBlock);

  const container = document.getElementById('test-root') || document.body;
  container.appendChild(blockOuter);
  return { codeBlock, blockOuter };
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
    addCodeBlockToDOM({ blockId: 'block-1', bottom: 100 });

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
    );
    expect(focus).toHaveBeenCalledOnce();
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
    addCodeBlockToDOM({ blockId: 'code-1', bottom: 100 });

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
    addCodeBlockToDOM({ blockId: 'block-2', bottom: 100 });

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
    addCodeBlockToDOM({ blockId: 'block-6', top: 100, bottom: 200 });

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
    );
    expect(focus).toHaveBeenCalledOnce();
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
    addCodeBlockToDOM({ blockId: 'code-7', top: 100, bottom: 200 });

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
    addCodeBlockToDOM({ blockId: 'code-7', top: 100, bottom: 200 });

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
    addCodeBlockToDOM({ blockId: 'code-a', top: 0, bottom: 100 });
    addCodeBlockToDOM({ blockId: 'code-b', top: 124, bottom: 224 });

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

  it('does not insert when clicking on code block content', () => {
    const insertBlocks = vi.fn();
    const editorRef = { current: { insertBlocks, focus: vi.fn(), setTextCursorPosition: vi.fn(), document: [] } };

    const container = render(React.createElement(TestHarness, { editorRef }));
    addCodeBlockToDOM({ blockId: 'block-3', bottom: 100 });

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
    addCodeBlockToDOM({ blockId: 'block-4', bottom: 100 });

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
    addCodeBlockToDOM({ blockId: 'block-r', bottom: 100 });

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
    expect(focus).toHaveBeenCalledTimes(2);
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
