import { useState, useEffect } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteSchema, defaultBlockSpecs } from '@blocknote/core';
import useArticle from '../hooks/useArticle';
import createHighlighter from '../utils/shiki-highlighter';
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

  var { audio: _a, file: _f, video: _v, ...keptSpecs } = defaultBlockSpecs;

  var editor = useCreateBlockNote({
    initialContent,
    schema: BlockNoteSchema.create({
      blockSpecs: {
        ...keptSpecs,
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
