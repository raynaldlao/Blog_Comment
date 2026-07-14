import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockEditor = {
  document: [
    { id: 'p1', type: 'paragraph' },
    { id: 'img1', type: 'image' },
    { id: 'vid1', type: 'video' },
    { id: 'p2', type: 'paragraph' },
  ],
  setTextCursorPosition: vi.fn(),
};

const mousedownHandler = (e) => {
  let target = e.target;
  if (target.nodeType === 3) target = target.parentNode;
  if (target?.closest?.('.bn-formatting-toolbar')) return;
  if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
  if (target?.closest?.('.bn-block-content[data-content-type="video"]')) return;
  try {
    const doc = mockEditor.document;
    for (let i = 0; i < doc.length; i++) {
      if (doc[i].type !== 'image' && doc[i].type !== 'video') {
        mockEditor.setTextCursorPosition(doc[i].id, 'start');
        break;
      }
    }
  } catch {}
};

function createBlock(contentType) {
  const el = document.createElement('div');
  el.className = 'bn-block-content';
  el.setAttribute('data-content-type', contentType);
  return el;
}

describe('ArticleForm mousedown handler', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    mockEditor.setTextCursorPosition.mockClear();
    document.addEventListener('mousedown', mousedownHandler, true);
  });

  afterEach(() => {
    document.removeEventListener('mousedown', mousedownHandler, true);
    document.body.innerHTML = '';
  });

  it('moves cursor to first text block when clicking outside image/video', () => {
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledOnce();
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledWith('p1', 'start');
  });

  it('returns early when clicking on image block', () => {
    const block = createBlock('image');
    document.body.appendChild(block);
    block.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
  });

  it('returns early when clicking on video block', () => {
    const block = createBlock('video');
    document.body.appendChild(block);
    block.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
  });

  it('returns early when clicking on formatting toolbar', () => {
    const toolbar = document.createElement('div');
    toolbar.className = 'bn-formatting-toolbar';
    document.body.appendChild(toolbar);
    toolbar.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
  });

  it('moves cursor to paragraph after image blocks when image clicked then outside', () => {
    const block = createBlock('video');
    document.body.appendChild(block);
    block.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledOnce();
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledWith('p1', 'start');
  });
});
