import React, { useState, useEffect } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteSchema, defaultBlockSpecs, createParagraphBlockSpec } from '@blocknote/core';
import useArticle from '../hooks/useArticle';
import createHighlighter from '../utils/shiki-highlighter-viewer';
import SUPPORTED_LANGUAGES from '../utils/supported-languages';
import { createCustomCodeBlockSpec } from '../utils/custom-code-block-spec';
import { createVideoOverrideSpec } from '../utils/video-override-spec';

function BlockNoteViewer({ initialContent }) {
  const [theme, setTheme] = useState(() =>
    document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
  );

  useEffect(() => {
    const el = document.documentElement;
    const observer = new MutationObserver(() => {
      setTheme(el.dataset.theme === 'dark' ? 'dark' : 'light');
    });
    observer.observe(el, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  useEffect(function () {
    var handler = function (e) {
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
    };
    document.addEventListener('copy', handler, true);
    return function () { document.removeEventListener('copy', handler, true); };
  }, []);

  useEffect(function () {
    if (!editor) return;
    var handler = function (e) {
      var target = e.target;
      if (target.nodeType === 3) target = target.parentNode;
      if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
      try {
        var doc = editor.document;
        for (var i = 0; i < doc.length; i++) {
          if (doc[i].type !== 'image' && doc[i].type !== 'video') {
            editor.setTextCursorPosition(doc[i].id, 'start');
            break;
          }
        }
      } catch {}
    };
    document.addEventListener('mousedown', handler, true);
    return function () { document.removeEventListener('mousedown', handler, true); };
  }, [editor]);

  var { audio: _a, file: _f, video: _v, ...keptSpecs } = defaultBlockSpecs;

  var editor = useCreateBlockNote({
    initialContent,
    schema: BlockNoteSchema.create({
      blockSpecs: {
        ...keptSpecs,
        paragraph: createParagraphBlockSpec(),
        image: defaultBlockSpecs.image,
        codeBlock: createCustomCodeBlockSpec({
          defaultLanguage: 'plaintext',
          supportedLanguages: SUPPORTED_LANGUAGES,
          createHighlighter: () => createHighlighter({
            themes: ['github-dark', 'github-light'],
            langs: [],
          }),
        }),
        video: createVideoOverrideSpec(),
      },
    }),
  });
  return <BlockNoteView editor={editor} theme={theme} editable={false} formattingToolbar={false} />;
}

export default function ArticleViewer() {
  const root = document.getElementById('root');
  const articleId = root?.dataset.articleId;

  const { loaded, contentStr, error } = useArticle(articleId);

  if (!loaded) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>;
  }

  let initialContent;
  try {
    initialContent = JSON.parse(contentStr);
  } catch {
    return <div className="alert alert-error">Unable to render article content.</div>;
  }

  return <BlockNoteViewer initialContent={initialContent} />;
}
