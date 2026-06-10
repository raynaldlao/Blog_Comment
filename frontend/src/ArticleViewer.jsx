import { useState, useEffect } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteSchema } from '@blocknote/core';
import { createHighlighter } from './shiki-highlighter';
import SUPPORTED_LANGUAGES from './supported-languages';
import { createCustomCodeBlockSpec } from './custom-code-block-spec';

function BlockNoteViewer({ initialContent }) {
  const editor = useCreateBlockNote({
    initialContent,
    schema: BlockNoteSchema.create().extend({
      blockSpecs: {
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
  return <BlockNoteView editor={editor} editable={false} />;
}

export default function ArticleViewer() {
  const root = document.getElementById('root');
  const articleId = root?.dataset.articleId;

  const [loaded, setLoaded] = useState(false);
  const [contentStr, setContentStr] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (articleId) {
      fetch(`/api/articles/${articleId}`)
        .then((r) => r.json())
        .then((data) => {
          setContentStr(data.content);
          setLoaded(true);
        })
        .catch(() => {
          setError('Failed to load article content.');
          setLoaded(true);
        });
    }
  }, [articleId]);

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
