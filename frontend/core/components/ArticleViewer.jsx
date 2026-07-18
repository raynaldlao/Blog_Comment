import React, { useState, useEffect } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteSchema, defaultBlockSpecs, createParagraphBlockSpec } from '@blocknote/core';
import useArticle from '../hooks/useArticle';
import createHighlighter from '../utils/shiki-highlighter-viewer';
import SUPPORTED_LANGUAGES from '../utils/supported-languages';
import { createCustomCodeBlockSpec } from '../utils/custom-code-block-spec';
import { createYouTubeVideoSpec } from '../utils/video-override-spec';


function BlockNoteViewer({ initialContent }) {
  const [theme, setTheme] = useState(() =>
    document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
  );

  useEffect(() => {
    const el = document.querySelector('.article-static-content');
    if (el) el.remove();
  }, []);

  useEffect(() => {
    const section = document.getElementById('comments-section');
    if (section) section.classList.remove('comments-hidden');
  }, []);

  useEffect(() => {
    const el = document.documentElement;
    const observer = new MutationObserver(() => {
      setTheme(el.dataset.theme === 'dark' ? 'dark' : 'light');
    });
    observer.observe(el, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const { audio: _a, file: _f, video: defaultVideoSpec, ...keptSpecs } = defaultBlockSpecs;

  const editor = useCreateBlockNote({
    initialContent,
    schema: BlockNoteSchema.create({
      blockSpecs: {
        ...keptSpecs,
        video: createYouTubeVideoSpec(defaultVideoSpec),
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
      },
    }),
  });

  useEffect(() => {
    const handler = (e) => {
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
    };
    document.addEventListener('copy', handler, true);
    return () => { document.removeEventListener('copy', handler, true); };
  }, []);

  useEffect(() => {
    if (!editor) return;
    const handler = (e) => {
      let target = e.target;
      if (target.nodeType === 3) target = target.parentNode;
      if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
      try {
        const doc = editor.document;
        for (let i = 0; i < doc.length; i++) {
          if (doc[i].type !== 'image' && doc[i].type !== 'video') {
            editor.setTextCursorPosition(doc[i].id, 'start');
            break;
          }
        }
      } catch {}
    };
    document.addEventListener('mousedown', handler, true);
    return () => { document.removeEventListener('mousedown', handler, true); };
  }, [editor]);

  return (
    <BlockNoteView
      editor={editor}
      theme={theme}
      editable={false}
      formattingToolbar={false}
      sideMenu={false}
      slashMenu={false}
      linkToolbar={false}
      filePanel={false}
      tableHandles={false}
      emojiPicker={false}
      comments={false}
    />
  );
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
