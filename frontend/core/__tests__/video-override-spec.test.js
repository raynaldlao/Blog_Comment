import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createVideoOverrideSpec } from '../utils/video-override-spec';

var mockConfig = {
  type: 'video',
  propSchema: {
    textAlignment: { default: 'left' },
    backgroundColor: { default: 'default' },
    name: { default: '' },
    url: { default: '' },
    caption: { default: '' },
    showPreview: { default: true },
    previewWidth: { default: undefined, type: 'number' },
  },
  content: 'none',
};

vi.mock('@blocknote/core', () => ({
  createVideoBlockConfig: vi.fn(function () { return mockConfig; }),
}));

var YT_URL = 'https://www.youtube.com/watch?v=eme8BnMFthI';
var YT_SHORT = 'https://youtu.be/eme8BnMFthI';
var YT_EMBED = 'https://www.youtube.com/embed/eme8BnMFthI';
var MP4_URL = 'https://example.com/video.mp4';

function createBlock(props) {
  return { props: props || {} };
}

function createEditor(resolveFileUrl) {
  return { isEditable: true, resolveFileUrl: resolveFileUrl || null };
}

beforeEach(function () {
  document.body.innerHTML = '';
});

afterEach(function () {
  document.body.innerHTML = '';
});

describe('createVideoOverrideSpec', function () {
  it('returns spec with config type video', function () {
    var spec = createVideoOverrideSpec();
    expect(spec.config.type).toBe('video');
    expect(spec.config.propSchema.url).toBeDefined();
    expect(spec.config.propSchema.url.default).toBe('');
    expect(spec.config.content).toBe('none');
  });

  it('returns spec with implementation.render function', function () {
    var spec = createVideoOverrideSpec();
    expect(spec.implementation).toHaveProperty('render');
    expect(typeof spec.implementation.render).toBe('function');
  });

  it('returns spec with fileBlockAccept meta', function () {
    var spec = createVideoOverrideSpec();
    expect(spec.implementation.meta.fileBlockAccept).toEqual(['video/*']);
  });
});

describe('render', function () {
  it('creates iframe for YouTube watch URL', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var iframe = result.dom.querySelector('iframe');
    expect(iframe).not.toBeNull();
    expect(iframe.src).toBe(YT_EMBED);
    expect(iframe.allow).toContain('fullscreen');
  });

  it('creates iframe for YouTube short URL', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_SHORT });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var iframe = result.dom.querySelector('iframe');
    expect(iframe).not.toBeNull();
    expect(iframe.src).toBe(YT_EMBED);
  });

  it('creates iframe for YouTube embed URL', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: 'https://www.youtube.com/embed/eme8BnMFthI' });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var iframe = result.dom.querySelector('iframe');
    expect(iframe).not.toBeNull();
    expect(iframe.src).toBe(YT_EMBED);
  });

  it('shows placeholder for non-YouTube URL', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: MP4_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    expect(result.dom.textContent).toBe('Only YouTube links are supported');
    expect(result.dom.querySelector('video')).toBeNull();
    expect(result.dom.querySelector('iframe')).toBeNull();
  });

  it('creates empty wrapper for empty url', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: '' });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    expect(result.dom.className).toBe('bn-visual-media-wrapper');
    expect(result.dom.children.length).toBe(0);
  });

  it('creates empty wrapper for null url', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: null });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    expect(result.dom.className).toBe('bn-visual-media-wrapper');
  });

  it('rejects non-YouTube URL and shows placeholder', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: 'https://vimeo.com/123456' });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    expect(result.dom.textContent).toBe('Only YouTube links are supported');
    expect(result.dom.querySelector('video')).toBeNull();
    expect(result.dom.querySelector('iframe')).toBeNull();
  });

  it('does not add allowfullscreen attribute (uses allow instead)', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var iframe = result.dom.querySelector('iframe');
    expect(iframe.hasAttribute('allowfullscreen')).toBe(false);
  });

  it('sets contentEditable=false on inner container', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var container = result.dom.querySelector('[contenteditable="false"]');
    expect(container).not.toBeNull();
    expect(container.parentElement.className).toBe('bn-visual-media-wrapper');
  });

  it('sets pointer-events:none on iframe when editor is editable', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var iframe = result.dom.querySelector('iframe');
    expect(iframe.style.pointerEvents).toBe('none');
  });

  it('does not set pointer-events on iframe when editor is not editable', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = { isEditable: false };
    var result = spec.implementation.render(block, editor);
    var iframe = result.dom.querySelector('iframe');
    expect(iframe.style.pointerEvents).toBe('');
  });

  it('removes pointer-events from iframe on dblclick', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var container = result.dom.firstElementChild;
    var iframe = result.dom.querySelector('iframe');

    container.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));

    expect(iframe.style.pointerEvents).toBe('');
  });

  it('restores pointer-events:none on click outside after dblclick', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var container = result.dom.firstElementChild;
    var iframe = result.dom.querySelector('iframe');

    container.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));

    expect(iframe.style.pointerEvents).toBe('none');
  });

  it('keeps pointer-events removed on click inside container after dblclick', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL });
    var editor = createEditor();
    var result = spec.implementation.render(block, editor);
    var container = result.dom.firstElementChild;
    var iframe = result.dom.querySelector('iframe');

    container.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    container.dispatchEvent(new MouseEvent('click', { bubbles: true }));

    expect(iframe.style.pointerEvents).toBe('');
  });
});

describe('toExternalHTML', function () {
  it('creates iframe for YouTube with showPreview', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL, showPreview: true });
    var result = spec.implementation.toExternalHTML(block);
    var iframe = result.dom;
    expect(iframe.tagName).toBe('IFRAME');
    expect(iframe.src).toBe(YT_EMBED);
    expect(iframe.width).toBe('560');
    expect(iframe.height).toBe('315');
  });

  it('creates link for YouTube without showPreview', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL, showPreview: false, name: 'My Video' });
    var result = spec.implementation.toExternalHTML(block);
    var link = result.dom;
    expect(link.tagName).toBe('A');
    expect(link.href).toContain(YT_URL);
    expect(link.textContent).toBe('My Video');
  });

  it('creates link from url when name is empty', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: YT_URL, showPreview: false });
    var result = spec.implementation.toExternalHTML(block);
    expect(result.dom.textContent).toBe(YT_URL);
  });

  it('shows placeholder for non-YouTube URL', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: MP4_URL });
    var result = spec.implementation.toExternalHTML(block);
    expect(result.dom.textContent).toBe('Only YouTube links are supported');
    expect(result.dom.tagName).not.toBe('VIDEO');
  });

  it('creates empty video for empty url', function () {
    var spec = createVideoOverrideSpec();
    var block = createBlock({ url: '' });
    var result = spec.implementation.toExternalHTML(block);
    expect(result.dom.tagName).toBe('VIDEO');
  });
});
