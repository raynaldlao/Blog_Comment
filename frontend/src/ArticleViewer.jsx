import { useState, useEffect } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';

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

  const editor = useCreateBlockNote({
    initialContent: loaded && contentStr ? JSON.parse(contentStr) : undefined,
  });

  if (!loaded) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>;
  }

  return <BlockNoteView editor={editor} editable={false} />;
}
