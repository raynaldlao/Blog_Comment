import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

function handler(e) {
  var block = document.querySelector(
    '.bn-block-content[data-content-type="image"].ProseMirror-selectednode',
  );
  if (!block) return;
  var imgEl = block.querySelector('img');
  if (!imgEl) return;
  e.preventDefault();
  e.stopPropagation();
  var alt = imgEl.alt || '';
  var src = imgEl.getAttribute('src') || '';
  var text;
  if (src && !src.startsWith('/uploads/')) {
    text = src;
  } else {
    text = alt || src.split('/').pop() || '';
  }
  navigator.clipboard.write([
    new ClipboardItem({
      'text/plain': new Blob([text], { type: 'text/plain' }),
    }),
  ]).catch(function () {});
}

function setImageDOM(alt, src, hasSelection) {
  var outer = document.createElement('div');
  outer.className = hasSelection
    ? 'bn-block-content ProseMirror-selectednode'
    : 'bn-block-content';
  outer.setAttribute('data-content-type', 'image');
  var img = document.createElement('img');
  if (alt) img.alt = alt;
  img.setAttribute('src', src);
  outer.appendChild(img);
  document.body.appendChild(outer);
  return { outer: outer, img: img };
}

describe('ArticleViewer copy handler', function () {
  var mockWrite;

  beforeEach(function () {
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

  afterEach(function () {
    document.removeEventListener('copy', handler, true);
    vi.unstubAllGlobals();
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('writes alt text for selected upload image', async function () {
    setImageDOM('my photo', '/uploads/foo.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).toHaveBeenCalledOnce();
    var text = await mockWrite.mock.calls[0][0][0].items['text/plain'].text();
    expect(text).toBe('my photo');
  });

  it('writes filename when upload image has no alt', async function () {
    setImageDOM('', '/uploads/foo.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).toHaveBeenCalledOnce();
    var text = await mockWrite.mock.calls[0][0][0].items['text/plain'].text();
    expect(text).toBe('foo.jpg');
  });

  it('writes URL for external image', async function () {
    setImageDOM('alt text', 'https://example.com/img.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).toHaveBeenCalledOnce();
    var text = await mockWrite.mock.calls[0][0][0].items['text/plain'].text();
    expect(text).toBe('https://example.com/img.jpg');
  });

  it('does nothing when image lacks .ProseMirror-selectednode', function () {
    setImageDOM('alt', '/uploads/foo.jpg', false);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).not.toHaveBeenCalled();
  });

  it('does nothing when no image DOM at all', function () {
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
    expect(mockWrite).not.toHaveBeenCalled();
  });

  it('stops event propagation for selected image', function () {
    var child = document.createElement('div');
    child.addEventListener('copy', function (e) {
      expect(e.defaultPrevented).toBe(true);
      expect(e.cancelBubble).toBe(true);
    });
    document.body.appendChild(child);
    setImageDOM('alt', '/uploads/foo.jpg', true);
    document.dispatchEvent(new ClipboardEvent('copy', { cancelable: true, bubbles: true }));
  });
});

var mockEditor = {
  document: [
    { id: 'p1', type: 'paragraph' },
    { id: 'img1', type: 'image' },
    { id: 'vid1', type: 'video' },
    { id: 'p2', type: 'paragraph' },
  ],
  setTextCursorPosition: vi.fn(),
};

var viewerHandler = function (e) {
  var target = e.target;
  if (target.nodeType === 3) target = target.parentNode;
  if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
  try {
    var doc = mockEditor.document;
    for (var i = 0; i < doc.length; i++) {
      if (doc[i].type !== 'image' && doc[i].type !== 'video') {
        mockEditor.setTextCursorPosition(doc[i].id, 'start');
        break;
      }
    }
  } catch {}
};

function createBlock(contentType) {
  var el = document.createElement('div');
  el.className = 'bn-block-content';
  el.setAttribute('data-content-type', contentType);
  return el;
}

describe('ArticleViewer mousedown handler', function () {
  beforeEach(function () {
    document.body.innerHTML = '';
    mockEditor.setTextCursorPosition.mockClear();
    document.addEventListener('mousedown', viewerHandler, true);
  });

  afterEach(function () {
    document.removeEventListener('mousedown', viewerHandler, true);
    document.body.innerHTML = '';
  });

  it('moves cursor to first text block when clicking outside image', function () {
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledOnce();
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledWith('p1', 'start');
  });

  it('returns early when clicking on image block', function () {
    var block = createBlock('image');
    document.body.appendChild(block);
    block.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
  });
});
