import { useState, useEffect } from 'react';

export default function useArticle(articleId) {
  const [loaded, setLoaded] = useState(!articleId);
  const [contentStr, setContentStr] = useState('');
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!articleId) {
      setLoaded(true);
      return;
    }
    (async () => {
      try {
        const r = await fetch(`/api/articles/${articleId}`);
        const data = await r.json();
        setTitle(data.title || '');
        setContentStr(data.content || '');
      } catch {
        setError('Failed to load article.');
      } finally {
        setLoaded(true);
      }
    })();
  }, [articleId]);

  return { loaded, contentStr, title, error };
}
