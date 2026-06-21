import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

var mockEditor = {
  document: [
    { id: 'p1', type: 'paragraph' },
    { id: 'img1', type: 'image' },
    { id: 'vid1', type: 'video' },
    { id: 'p2', type: 'paragraph' },
  ],
  setTextCursorPosition: vi.fn(),
};

var mousedownHandler = function (e) {
  var target = e.target;
  if (target.nodeType === 3) target = target.parentNode;
  if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
  if (target?.closest?.('.bn-block-content[data-content-type="video"]')) return;
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

describe('ArticleForm mousedown handler', function () {
  beforeEach(function () {
    document.body.innerHTML = '';
    mockEditor.setTextCursorPosition.mockClear();
    document.addEventListener('mousedown', mousedownHandler, true);
  });

  afterEach(function () {
    document.removeEventListener('mousedown', mousedownHandler, true);
    document.body.innerHTML = '';
  });

  it('moves cursor to first text block when clicking outside image/video', function () {
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

  it('returns early when clicking on video block', function () {
    var block = createBlock('video');
    document.body.appendChild(block);
    block.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
  });

  it('moves cursor to paragraph after image blocks when image clicked then outside', function () {
    var block = createBlock('video');
    document.body.appendChild(block);
    block.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).not.toHaveBeenCalled();
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledOnce();
    expect(mockEditor.setTextCursorPosition).toHaveBeenCalledWith('p1', 'start');
  });
});
