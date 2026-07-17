const YOUTUBE_RE = /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;

function isYouTubeUrl(url) {
  return YOUTUBE_RE.test(url);
}

function getYouTubeEmbedUrl(url) {
  const m = url.match(YOUTUBE_RE);
  return m ? 'https://www.youtube.com/embed/' + m[1] : null;
}

function buildYouTubeIFrame(url, isEditable) {
  const embedUrl = getYouTubeEmbedUrl(url);

  const wrapper = document.createElement('div');
  wrapper.className = 'bn-visual-media-wrapper';
  wrapper.style.cssText = 'position:relative;width:100%;aspect-ratio:16/9';

  const iframe = document.createElement('iframe');
  iframe.src = embedUrl;
  iframe.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:4px';
  iframe.allow = 'fullscreen; accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';

  if (isEditable) {
    iframe.style.pointerEvents = 'none';

    wrapper.addEventListener('click', (e) => {
      e.stopPropagation();
      iframe.style.pointerEvents = '';
      if (iframe.contentWindow) iframe.contentWindow.focus();

      const onAnyClick = (e) => {
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
  const old = document.querySelector('.toast');
  if (old) old.remove();
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => { if (el.parentNode) el.remove(); }, 2800);
}

export function createYouTubeVideoSpec(videoSpec) {
  const origRender = videoSpec.implementation.render;
  const origToExternalHTML = videoSpec.implementation.toExternalHTML;

  return {
    ...videoSpec,
    implementation: {
      ...videoSpec.implementation,
      render: function (block, editor) {
        const url = block.props.url;

        if (url && isYouTubeUrl(url)) {
          const contentDiv = document.createElement('div');
          contentDiv.className = 'bn-block-content';
          contentDiv.dataset.contentType = 'video';
          contentDiv.dataset.fileBlock = '';
          contentDiv.dataset.url = url;
          contentDiv.draggable = 'true';

          const iframeContainer = buildYouTubeIFrame(url, editor.isEditable);
          contentDiv.appendChild(iframeContainer);

          return { dom: contentDiv };
        }

        if (url && editor.isEditable) {
          showToast('Only YouTube links are supported');
          setTimeout(() => { editor.removeBlocks([block.id]); }, 0);
          const empty = document.createElement('div');
          empty.style.cssText = 'display:none';
          return { dom: empty };
        }

        if (url) {
          const empty = document.createElement('div');
          empty.style.cssText = 'display:none';
          return { dom: empty };
        }

        const result = origRender.call(this, block, editor);
        if (!editor.isEditable && result && result.dom) {
          const textEl = result.dom.querySelector('.bn-add-file-button-text');
          if (textEl) textEl.textContent = 'Add YouTube video URL';
        }
        return result;
      },
      toExternalHTML: function (block) {
        const url = block.props && block.props.url;

        if (!url || !isYouTubeUrl(url)) {
          return origToExternalHTML.call(this, block);
        }

        const embedUrl = getYouTubeEmbedUrl(url);
        const iframe = document.createElement('iframe');
        iframe.src = embedUrl;
        iframe.width = '560';
        iframe.height = '315';
        return { dom: iframe };
      },
    },
  };
}
