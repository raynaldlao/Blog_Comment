import { useState, useEffect } from 'react';

export default function useArticle(articleId) {
  const ssrEl = typeof document !== 'undefined'
    ? document.getElementById('article-data') : null;
  const ssrContent = ssrEl ? ssrEl.textContent : null;

  const [loaded, setLoaded] = useState(!articleId || !!ssrContent);
  const [contentStr, setContentStr] = useState(ssrContent || '');
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!articleId) {
      setLoaded(true);
      return;
    }
    if (ssrContent) {
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
