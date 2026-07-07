import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { createYouTubeVideoSpec } from '../utils/video-override-spec';

function makeBlock(url) {
  return { id: 'b1', props: { url: url } };
}

function makeEditor(editable) {
  return { isEditable: editable, removeBlocks: vi.fn() };
}

describe('createYouTubeVideoSpec', function () {
  var origRender, origToExternalHTML, videoSpec;

  beforeEach(function () {
    document.querySelectorAll('.toast').forEach(function (t) { t.remove(); });
    origRender = vi.fn(function () {
      return { dom: document.createElement('div') };
    });
    origToExternalHTML = vi.fn(function () {
      return { dom: document.createElement('a') };
    });
    videoSpec = {
      implementation: { render: origRender, toExternalHTML: origToExternalHTML },
    };
    vi.useFakeTimers();
  });

  afterEach(function () {
    document.querySelectorAll('.toast').forEach(function (t) { t.remove(); });
    vi.useRealTimers();
  });

  it('returns spec with same shape', function () {
    var spec = createYouTubeVideoSpec(videoSpec);
    expect(spec).toHaveProperty('implementation');
    expect(spec.implementation).toHaveProperty('render');
    expect(spec.implementation).toHaveProperty('toExternalHTML');
  });

  describe('render', function () {
    it('returns bn-block-content with iframe for YouTube URL', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(true);
      var result = spec.implementation.render(makeBlock('https://www.youtube.com/watch?v=eme8BnMFthI'), editor);

      expect(result.dom.className).toContain('bn-block-content');
      expect(result.dom.querySelector('iframe')).toBeTruthy();
      expect(result.dom.querySelector('iframe').src).toContain('youtube.com/embed/');
      expect(origRender).not.toHaveBeenCalled();
    });

    it('returns iframe without pointerEvents in viewer', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(false);
      var result = spec.implementation.render(makeBlock('https://youtu.be/abcdefghijk'), editor);

      var iframe = result.dom.querySelector('iframe');
      expect(iframe.style.pointerEvents).toBe('');
    });

    it('shows toast and calls removeBlocks for non-YouTube URL in editor', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(true);
      spec.implementation.render(makeBlock('https://vimeo.com/123'), editor);

      vi.advanceTimersByTime(0);

      expect(origRender).not.toHaveBeenCalled();

      var toast = document.querySelector('.toast');
      expect(toast).toBeTruthy();
      expect(toast.textContent).toContain('Only YouTube');

      expect(editor.removeBlocks).toHaveBeenCalledWith(['b1']);
    });

    it('returns display:none div for non-YouTube URL in viewer', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(false);
      var result = spec.implementation.render(makeBlock('https://vimeo.com/123'), editor);

      expect(result.dom.style.display).toBe('none');
      expect(origRender).not.toHaveBeenCalled();
      expect(document.querySelector('.toast')).toBeNull();
    });

    it('calls origRender when url is empty', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(true);
      var result = spec.implementation.render(makeBlock(''), editor);

      expect(origRender).toHaveBeenCalledTimes(1);
    });

    it('calls origRender when url is undefined', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(true);
      var block = { id: 'b1', props: {} };
      var result = spec.implementation.render(block, editor);

      expect(origRender).toHaveBeenCalledTimes(1);
    });

    it('calls origRender when url is null', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var editor = makeEditor(true);
      var result = spec.implementation.render(makeBlock(null), editor);

      expect(origRender).toHaveBeenCalledTimes(1);
    });
  });

  describe('toExternalHTML', function () {
    it('returns iframe for YouTube URL', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var result = spec.implementation.toExternalHTML(makeBlock('https://www.youtube.com/watch?v=eme8BnMFthI'));

      expect(result.dom.tagName).toBe('IFRAME');
      expect(result.dom.src).toContain('youtube.com/embed/');
      expect(origToExternalHTML).not.toHaveBeenCalled();
    });

    it('calls origToExternalHTML for non-YouTube URL', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var result = spec.implementation.toExternalHTML(makeBlock('https://vimeo.com/123'));

      expect(origToExternalHTML).toHaveBeenCalledTimes(1);
    });

    it('calls origToExternalHTML when url is empty', function () {
      var spec = createYouTubeVideoSpec(videoSpec);
      var result = spec.implementation.toExternalHTML(makeBlock(''));

      expect(origToExternalHTML).toHaveBeenCalledTimes(1);
    });
  });
});
