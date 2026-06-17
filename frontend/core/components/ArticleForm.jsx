import { useState, useEffect, useRef, useCallback } from 'react';
import { useCreateBlockNote, FormattingToolbarController, useEditorSelectionChange } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteSchema, defaultBlockSpecs } from '@blocknote/core';
import CustomFormattingToolbar from './CustomFormattingToolbar';
import useArticle from '../hooks/useArticle';
import useCodeBlockGapClick from '../hooks/useCodeBlockGapClick';
import createHighlighter from '../utils/shiki-highlighter';
import SUPPORTED_LANGUAGES from '../utils/supported-languages';
import { createCustomCodeBlockSpec } from '../utils/custom-code-block-spec';
import { createVideoOverrideSpec } from '../utils/video-override-spec';


export function applyVideoDictOverrides(editor) {
  editor.dictionary.slash_menu.video.title = 'YouTube';
  editor.dictionary.slash_menu.video.subtext = 'Paste a YouTube video URL';
  editor.dictionary.slash_menu.video.aliases = [
    'youtube', 'yt', 'video', 'videoUpload', 'upload', 'film', 'media', 'url',
  ];
  editor.dictionary.file_panel.embed.title = 'YouTube URL';
  editor.dictionary.file_panel.embed.url_placeholder = 'Paste YouTube video link';
  editor.dictionary.file_panel.embed.embed_button.video = 'Embed YouTube video';
}

function BlockNoteEditor({ initialContent, onReady }) {
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

  const uploadFn = useCallback(async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/upload/image', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Upload failed.');
    }
    const data = await res.json();
    return data.url;
  }, []);

  var { audio: _a, file: _f, video: _v, ...keptSpecs } = defaultBlockSpecs;

  var editor = useCreateBlockNote({
    initialContent,
    uploadFile: uploadFn,
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

  useEffect(function () {
    if (editor) applyVideoDictOverrides(editor);
  }, [editor]);

  const handleSelectionChange = useCallback(() => {
    try {
      const { block } = editor.getTextCursorPosition();
      if (block?.type !== 'image') {
        editor.uploadFile = undefined;
        editor.portalElement?.classList.remove('image-selected');
      } else {
        if (!editor.uploadFile) {
          editor.uploadFile = uploadFn;
        }
        editor.portalElement?.classList.add('image-selected');
      }
    } catch {
      editor.uploadFile = undefined;
      editor.portalElement?.classList.remove('image-selected');
    }
  }, [editor, uploadFn]);

  useEditorSelectionChange(handleSelectionChange, editor);

  useEffect(() => {
    if (editor && onReady) onReady(editor);
  }, [editor, onReady]);

  return (
    <BlockNoteView
      editor={editor}
      theme={theme}
      formattingToolbar={false}
    >
      <FormattingToolbarController formattingToolbar={CustomFormattingToolbar} />
    </BlockNoteView>
  );
}

export default function ArticleForm() {
  const root = document.getElementById('root');
  const page = root?.dataset.page;
  const articleId = root?.dataset.articleId;

  const { loaded, contentStr, title: loadedTitle, error: loadError } = useArticle(
    page === 'edit' ? articleId : null,
  );
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const editorRef = useRef(null);

  useEffect(() => {
    if (loadedTitle) setTitle(loadedTitle);
  }, [loadedTitle]);

  useCodeBlockGapClick(editorRef);

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('Title is required.');
      return;
    }
    setSaving(true);
    setError('');

    const url = page === 'create' ? '/api/articles' : `/api/articles/${articleId}`;
    const method = page === 'create' ? 'POST' : 'PUT';
    const content = JSON.stringify(editorRef.current.document);

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

  const displayError = error || loadError;

  let initialContent;
  try {
    initialContent = contentStr ? JSON.parse(contentStr) : undefined;
  } catch {
    return <div className="alert alert-error">Unable to parse article content.</div>;
  }

  return (
    <div className="article-editor">
      {displayError && <div className="alert alert-error">{displayError}</div>}
      <input
        type="text"
        className="article-editor-title"
        placeholder="Article title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <BlockNoteEditor initialContent={initialContent} onReady={(ed) => { editorRef.current = ed; }} />
      <div className="article-editor-actions">
        <button className="btn" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Saving...' : page === 'create' ? 'Publish' : 'Save'}
        </button>
      </div>
    </div>
  );
}
