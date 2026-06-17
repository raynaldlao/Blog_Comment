import { createVideoBlockConfig } from '@blocknote/core';

var YOUTUBE_RE = /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;

function isYouTubeUrl(url) {
  return YOUTUBE_RE.test(url);
}

function getYouTubeEmbedUrl(url) {
  var m = url.match(YOUTUBE_RE);
  return m ? 'https://www.youtube.com/embed/' + m[1] : null;
}

function mediaWrapper(domElement) {
  var wrapper = document.createElement('div');
  wrapper.className = 'bn-visual-media-wrapper';
  wrapper.appendChild(domElement);
  return { dom: wrapper };
}

export function createVideoOverrideSpec() {
  var config = createVideoBlockConfig({});

  return {
    config: config,
    implementation: {
      meta: {
        fileBlockAccept: ['video/*'],
      },
      render(block, editor) {
        var url = block.props.url;

        if (!url) {
          var wrapper = document.createElement('div');
          wrapper.className = 'bn-visual-media-wrapper';
          return { dom: wrapper };
        }

        if (isYouTubeUrl(url)) {
          var embedUrl = getYouTubeEmbedUrl(url);
          var iframeContainer = document.createElement('div');
          iframeContainer.style.cssText = 'position:relative;width:100%;aspect-ratio:16/9';
          iframeContainer.contentEditable = 'false';

          var iframe = document.createElement('iframe');
          iframe.src = embedUrl;
          iframe.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:4px';
          iframe.allow = 'fullscreen; accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';

          if (editor.isEditable) {
            iframe.style.pointerEvents = 'none';

            iframeContainer.addEventListener('dblclick', function () {
              iframe.style.pointerEvents = '';
              if (iframe.contentWindow) iframe.contentWindow.focus();

              var onAnyClick = function (e) {
                if (!iframeContainer.contains(e.target)) {
                  iframe.style.pointerEvents = 'none';
                  document.removeEventListener('click', onAnyClick, true);
                }
              };
              document.addEventListener('click', onAnyClick, true);
            });
          }

          iframeContainer.appendChild(iframe);

          return mediaWrapper(iframeContainer);
        }

        var msg = document.createElement('div');
        msg.className = 'bn-visual-media-wrapper';
        msg.style.cssText = 'display:flex;align-items:center;justify-content:center;padding:2rem;color:#888';
        msg.textContent = 'Only YouTube links are supported';
        return { dom: msg };
      },
      toExternalHTML(block) {
        var url = block.props.url;

        if (!url) {
          return { dom: document.createElement('video') };
        }

        if (isYouTubeUrl(url)) {
          var embedUrl = getYouTubeEmbedUrl(url);
          if (block.props.showPreview) {
            var iframe = document.createElement('iframe');
            iframe.src = embedUrl;
            iframe.width = '560';
            iframe.height = '315';
            return { dom: iframe };
          }
          var link = document.createElement('a');
          link.href = url;
          link.textContent = block.props.name || url;
          return { dom: link };
        }

        var msg = document.createElement('div');
        msg.textContent = 'Only YouTube links are supported';
        return { dom: msg };
      },
    },
  };
}
