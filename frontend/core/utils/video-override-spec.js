var YOUTUBE_RE = /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;

function isYouTubeUrl(url) {
  return YOUTUBE_RE.test(url);
}

function getYouTubeEmbedUrl(url) {
  var m = url.match(YOUTUBE_RE);
  return m ? 'https://www.youtube.com/embed/' + m[1] : null;
}

function buildYouTubeIFrame(url, isEditable) {
  var embedUrl = getYouTubeEmbedUrl(url);

  var wrapper = document.createElement('div');
  wrapper.className = 'bn-visual-media-wrapper';
  wrapper.style.cssText = 'position:relative;width:100%;aspect-ratio:16/9';

  var iframe = document.createElement('iframe');
  iframe.src = embedUrl;
  iframe.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:4px';
  iframe.allow = 'fullscreen; accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';

  if (isEditable) {
    iframe.style.pointerEvents = 'none';

    wrapper.addEventListener('dblclick', function () {
      iframe.style.pointerEvents = '';
      if (iframe.contentWindow) iframe.contentWindow.focus();

      var onAnyClick = function (e) {
        if (!wrapper.contains(e.target)) {
          iframe.style.pointerEvents = 'none';
          document.removeEventListener('click', onAnyClick, true);
        }
      };
      document.addEventListener('click', onAnyClick, true);
    });
  }

  wrapper.appendChild(iframe);
  return wrapper;
}

function showToast(msg) {
  var old = document.querySelector('.toast');
  if (old) old.remove();
  var el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(function () { if (el.parentNode) el.remove(); }, 2800);
}

export function createYouTubeVideoSpec(videoSpec) {
  var origRender = videoSpec.implementation.render;
  var origToExternalHTML = videoSpec.implementation.toExternalHTML;

  return {
    ...videoSpec,
    implementation: {
      ...videoSpec.implementation,
      render: function (block, editor) {
        var url = block.props.url;

        if (url && isYouTubeUrl(url)) {
          var contentDiv = document.createElement('div');
          contentDiv.className = 'bn-block-content';
          contentDiv.dataset.contentType = 'video';
          contentDiv.dataset.fileBlock = '';
          contentDiv.dataset.url = url;
          contentDiv.draggable = 'true';

          var iframeContainer = buildYouTubeIFrame(url, editor.isEditable);
          contentDiv.appendChild(iframeContainer);

          return { dom: contentDiv };
        }

        if (url && editor.isEditable) {
          showToast('Only YouTube links are supported');
          setTimeout(function () { editor.removeBlocks([block.id]); }, 0);
          var empty = document.createElement('div');
          empty.style.cssText = 'display:none';
          return { dom: empty };
        }

        if (url) {
          var empty = document.createElement('div');
          empty.style.cssText = 'display:none';
          return { dom: empty };
        }

        var result = origRender.call(this, block, editor);
        if (!editor.isEditable && result && result.dom) {
          var textEl = result.dom.querySelector('.bn-add-file-button-text');
          if (textEl) textEl.textContent = 'Add YouTube video URL';
        }
        return result;
      },
      toExternalHTML: function (block) {
        var url = block.props && block.props.url;

        if (!url || !isYouTubeUrl(url)) {
          return origToExternalHTML.call(this, block);
        }

        var embedUrl = getYouTubeEmbedUrl(url);
        var iframe = document.createElement('iframe');
        iframe.src = embedUrl;
        iframe.width = '560';
        iframe.height = '315';
        return { dom: iframe };
      },
    },
  };
}
