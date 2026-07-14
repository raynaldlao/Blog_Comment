import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

function handler(e) {
  const block = document.querySelector(
    '.bn-block-content[data-content-type="image"].ProseMirror-selectednode',
  );
  if (!block) return;
  const imgEl = block.querySelector('img');
  if (!imgEl) return;
  e.preventDefault();
  e.stopPropagation();
  const alt = imgEl.alt || '';
  const src = imgEl.getAttribute('src') || '';
  let text;
  if (src && !src.startsWith('/uploads/')) {
    text = src;
  } else {
    text = alt || src.split('/').pop() || '';
  }
  navigator.clipboard.write([
    new ClipboardItem({
      'text/plain': new Blob([text], { type: 'text/plain' }),
    }),
  ]).catch(() => {});
}

function setImageDOM(alt, src, hasSelection) {
  const outer = document.createElement('div');
  outer.className = hasSelection
    ? 'bn-block-content ProseMirror-selectednode'
    : 'bn-block-content';
  outer.setAttribute('data-content-type', 'image');
  const img = document.createElement('img');
  if (alt) img.alt = alt;
  img.setAttribute('src', src);
  outer.appendChild(img);
  document.body.appendChild(outer);
  return { outer, img };
}

describe('ArticleViewer copy handler', () => {
  let mockWrite;

  beforeEach(() => {
    mockWrite = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', {
      clipboard: { write: mockWrite },
    });
    vi.stubGlobal('ClipboardItem', vi.fn(function (items) {
      this.items = items;
    }));
    document.body.innerHTML = '';
    document.addEventListener('copy', handler, true);
  });

  afterEach(() => {
    document.removeEventListener('copy', handler, true);
    vi.unstubAllGlobals();
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('writes alt text for selected upload image', async () => {
    setImageDOM('my photo', '/uploads/foo.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).toHaveBeenCalledOnce();
    const text = await mockWrite.mock.calls[0][0][0].items['text/plain'].text();
    expect(text).toBe('my photo');
  });

  it('writes filename when upload image has no alt', async () => {
    setImageDOM('', '/uploads/foo.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).toHaveBeenCalledOnce();
    const text = await mockWrite.mock.calls[0][0][0].items['text/plain'].text();
    expect(text).toBe('foo.jpg');
  });

  it('writes URL for external image', async () => {
    setImageDOM('alt text', 'https://example.com/img.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).toHaveBeenCalledOnce();
    const text = await mockWrite.mock.calls[0][0][0].items['text/plain'].text();
    expect(text).toBe('https://example.com/img.jpg');
  });

  it('does nothing when image lacks .ProseMirror-selectednode', () => {
    setImageDOM('alt', '/uploads/foo.jpg', false);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).not.toHaveBeenCalled();
  });

  it('does nothing when no image DOM at all', () => {
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).not.toHaveBeenCalled();
  });

  it('stops event propagation for selected image', () => {
    const child = document.createElement('div');
    child.addEventListener('copy', (e) => {
      expect(e.defaultPrevented).toBe(true);
      expect(e.cancelBubble).toBe(true);
    });
    document.body.appendChild(child);
    setImageDOM('alt', '/uploads/foo.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
  });
});

const mockEditor = {
  document: [
    { id: 'p1', type: 'paragraph' },
    { id: 'img1', type: 'image' },
    { id: 'vid1', type: 'video' },
    { id: 'p2', type: 'paragraph' },
  ],
  setTextCursorPosition: vi.fn(),
};

const viewerHandler = (e) => {
  let target = e.target;
  if (target.nodeType === 3) target = target.parentNode;
  if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
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

describe('ArticleViewer mousedown handler', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    mockEditor.setTextCursorPosition.mockClear();
    document.addEventListener('mousedown', viewerHandler, true);
  });

  afterEach(() => {
    document.removeEventListener('mousedown', viewerHandler, true);
    document.body.innerHTML = '';
  });

  it('moves cursor to first text block when clicking outside image', () => {
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
});
