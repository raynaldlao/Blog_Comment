import React from 'react';
import { useBlockNoteEditor, useComponentsContext } from '@blocknote/react';

export default function CopyBlockButton() {
  const editor = useBlockNoteEditor();
  const Components = useComponentsContext();
  if (!editor || !Components) return null;

  let block;
  try {
    block = editor.getSelection()?.blocks?.[0] ?? editor.getTextCursorPosition().block;
  } catch { return null; }

  if (!block) return null;

  return (
    <Components.FormattingToolbar.Button
      mainTooltip={block.type === 'image' || block.type === 'video' ? 'Copy' : 'Copy Block'}
      onClick={() => {
        const data = { type: block.type, props: block.props, content: block.content };
        const html = '<blocknote-block data-json=\'' + JSON.stringify(data).replace(/'/g, '&apos;') + '\'></blocknote-block>';
        let plainText = '';
        if (block.type === 'image') {
          if (block.props?.url && !block.props.url.startsWith('/uploads/')) {
            plainText = block.props.url;
          } else {
            plainText = block.props?.alt || block.props?.name || '';
          }
        } else if (block.type === 'video') {
          plainText = block.props?.url || '';
        } else {
          plainText = block.props?.url || '';
        }
        const items = {
          'text/plain': new Blob([plainText], { type: 'text/plain' }),
          'text/html': new Blob([html], { type: 'text/html' }),
        };
        navigator.clipboard.write([new ClipboardItem(items)]).catch(() => {});
        const old = document.querySelector('.toast');
        if (old) old.remove();
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = 'Copied to clipboard';
        document.body.appendChild(toast);
        setTimeout(() => { if (toast.parentElement) toast.remove(); }, 2800);
      }}
      icon={
        <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 24 24" height="1em" width="1em">
          <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
        </svg>
      }
    />
  );
}
