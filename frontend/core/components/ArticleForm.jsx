import { useState, useEffect, useRef, useCallback } from 'react';
import { offset } from '@floating-ui/react';
import { useCreateBlockNote, FormattingToolbarController, useEditorSelectionChange, SideMenuController, SideMenu, FilePanelController, FilePanel, UploadTab, EmbedTab, useBlockNoteEditor } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteSchema, defaultBlockSpecs, createParagraphBlockSpec } from '@blocknote/core';
import CustomFormattingToolbar from './CustomFormattingToolbar';
import CustomDragHandleMenu from './CustomDragHandleMenu';
import useArticle from '../hooks/useArticle';
import useCodeBlockGapClick from '../hooks/useCodeBlockGapClick';
import createHighlighter from '../utils/shiki-highlighter-editor';
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

function CustomFilePanel({ blockId }) {
  const editor = useBlockNoteEditor();
  const [loading, setLoading] = useState(false);
  let block;
  try {
    block = blockId ? editor.getBlock(blockId) : null;
  } catch {
    block = null;
  }
  if (block?.type === 'image') {
    return (
      <FilePanel
        blockId={blockId}
        tabs={[{
          name: 'Upload',
          tabPanel: <UploadTab blockId={blockId} setLoading={setLoading} />,
        }]}
      />
    );
  }
  if (block?.type === 'video') {
    return (
      <FilePanel
        blockId={blockId}
        tabs={[{
          name: 'YouTube URL',
          tabPanel: <EmbedTab blockId={blockId} />,
        }]}
      />
    );
  }
  return <FilePanel blockId={blockId} />;
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

  const { audio: _a, file: _f, video: _v, ...keptSpecs } = defaultBlockSpecs;

  const editor = useCreateBlockNote({
    initialContent,
    uploadFile: uploadFn,
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

  useEffect(function () {
    if (editor) applyVideoDictOverrides(editor);
  }, [editor]);

  const handleSelectionChange = useCallback(() => {
    try {
      const { block } = editor.getTextCursorPosition();
      if (block?.type === 'image') {
        editor.portalElement?.classList.add('image-selected');
      } else {
        editor.portalElement?.classList.remove('image-selected');
      }
    } catch {
      editor.portalElement?.classList.remove('image-selected');
    }
  }, [editor]);

  useEditorSelectionChange(handleSelectionChange, editor);

  useEffect(() => {
    if (editor && onReady) onReady(editor);
  }, [editor, onReady]);

  useEffect(() => {
    if (!editor) return;
    const handler = (e) => {
      const mod = e.ctrlKey || e.metaKey;
      if (!mod || (e.key !== 'z' && e.key !== 'y')) return;
      const editorEl = editor.dom?.closest('.bn-editor') || editor.dom;
      if (editorEl?.contains(document.activeElement)) return;
      e.preventDefault();
      if (e.key === 'z' && !e.shiftKey) editor.undo();
      else if (e.key === 'y' || (e.key === 'z' && e.shiftKey)) editor.redo();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [editor]);

  useEffect(() => {
    if (!editor) return;
    const handler = function (e) {
      const html = e.clipboardData.getData('text/html');
      if (html && html.includes('blocknote-block')) {
        e.preventDefault();
        e.stopPropagation();
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        const el = tmp.querySelector('blocknote-block');
        if (!el) return;
        const data = JSON.parse(el.getAttribute('data-json'));
        let block;
        try { block = editor.getTextCursorPosition().block; }
        catch { return; }
        editor.updateBlock(block, data);
        if (data.type === 'image') {
          document.querySelectorAll('.ProseMirror-selectednode').forEach(function (el) {
            el.classList.remove('ProseMirror-selectednode');
          });
          editor.domElement?.blur();
        }
        if (data.type === 'video') {
          document.querySelectorAll('.ProseMirror-selectednode').forEach(function (el) {
            el.classList.remove('ProseMirror-selectednode');
          });
          try {
            const doc = editor.document;
            if (doc) {
              for (let i = 0; i < doc.length; i++) {
                if (doc[i].type !== 'video' && doc[i].type !== 'image') {
                  editor.setTextCursorPosition(doc[i].id, 'start');
                  break;
                }
              }
            }
          } catch {}
        }
      }
      requestAnimationFrame(function () {
        document.querySelectorAll('.ProseMirror-selectednode').forEach(function (el) {
          el.classList.remove('ProseMirror-selectednode');
        });
      });
    };
    document.addEventListener('paste', handler, true);
    return () => document.removeEventListener('paste', handler, true);
  }, [editor]);

  useEffect(() => {
    if (!editor) return;
    const handler = function (e) {
      let block;
      try { block = editor.getSelection()?.blocks?.[0] ?? editor.getTextCursorPosition().block; }
      catch { return; }
      if (!block || (block.type !== 'image' && block.type !== 'video')) return;
      e.preventDefault();
      e.stopPropagation();
      const data = { type: block.type, props: block.props, content: block.content };
      const html = '<blocknote-block data-json=\'' + JSON.stringify(data).replace(/'/g, '&apos;') + '\'></blocknote-block>';
      let text;
      if (block.type === 'image') {
        if (block.props?.url && !block.props.url.startsWith('/uploads/')) {
          text = block.props.url;
        } else {
          text = block.props?.alt || block.props?.name || '';
        }
      } else {
        text = block.props?.url || '';
      }
      const items = {
        'text/plain': new Blob([text], { type: 'text/plain' }),
        'text/html': new Blob([html], { type: 'text/html' }),
      };
      navigator.clipboard.write([new ClipboardItem(items)]).catch(function () {});
    };
    document.addEventListener('copy', handler, true);
    return () => document.removeEventListener('copy', handler, true);
  }, [editor]);

  useEffect(function () {
    if (!editor) return;
    const handler = function (e) {
      let target = e.target;
      if (target.nodeType === 3) target = target.parentNode;
      if (target?.closest?.('.bn-formatting-toolbar, .bn-panel')) return;
      if (target?.closest?.('.bn-block-content[data-content-type="image"]')) return;
      if (target?.closest?.('.bn-block-content[data-content-type="video"]')) return;
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
    return function () { document.removeEventListener('mousedown', handler, true); };
  }, [editor]);

  return (
    <BlockNoteView
      editor={editor}
      theme={theme}
      formattingToolbar={false}
      sideMenu={false}
      filePanel={false}
    >
      <FormattingToolbarController formattingToolbar={CustomFormattingToolbar} />
      <SideMenuController
        sideMenu={(props) => (
          <SideMenu {...props} dragHandleMenu={CustomDragHandleMenu} />
        )}
        floatingUIOptions={{
          useFloatingOptions: {
            middleware: [offset(10)],
          },
        }}
      />
      <FilePanelController filePanel={CustomFilePanel} />
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
