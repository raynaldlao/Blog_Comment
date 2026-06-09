import { useState, useEffect } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';

export default function ArticleEditor() {
  const root = document.getElementById('root');
  const page = root?.dataset.page;
  const articleId = root?.dataset.articleId;

  const [loaded, setLoaded] = useState(page !== 'edit');
  const [title, setTitle] = useState('');
  const [contentStr, setContentStr] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (page === 'edit' && articleId) {
      fetch(`/api/articles/${articleId}`)
        .then((r) => r.json())
        .then((data) => {
          setTitle(data.title);
          setContentStr(data.content);
          setLoaded(true);
        })
        .catch(() => {
          setError('Failed to load article.');
          setLoaded(true);
        });
    }
  }, [page, articleId]);

  const editor = useCreateBlockNote({
    initialContent: loaded && contentStr ? JSON.parse(contentStr) : undefined,
  });

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('Title is required.');
      return;
    }
    setSaving(true);
    setError('');

    const url = page === 'create' ? '/api/articles' : `/api/articles/${articleId}`;
    const method = page === 'create' ? 'POST' : 'PUT';
    const content = JSON.stringify(editor.document);

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });

      if (res.ok) {
        const data = await res.json();
        window.location.href = `/articles/${data.id || articleId}`;
      } else {
        const err = await res.json();
        setError(err.error || 'Failed to save.');
        setSaving(false);
      }
    } catch {
      setError('Network error.');
      setSaving(false);
    }
  };

  if (!loaded) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="article-editor">
      {error && <div className="alert alert-error">{error}</div>}
      <input
        type="text"
        className="article-editor-title"
        placeholder="Article title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <BlockNoteView editor={editor} />
      <div className="article-editor-actions">
        <button className="btn" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Saving...' : page === 'create' ? 'Publish' : 'Save'}
        </button>
      </div>
    </div>
  );
}
