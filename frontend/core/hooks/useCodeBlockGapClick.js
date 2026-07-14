import { useEffect, useRef } from 'react';

const GAP_SIZE = 12;

export default function useCodeBlockGapClick(editorRef) {
  const lastInsertedRef = useRef({ key: '', time: 0 });

  useEffect(() => {
    const handler = (e) => {
      const editor = editorRef.current;
      if (!editor || !editor._tiptapEditor) return;

      if (e.key === 'Backspace' && !e.isComposing) {
        const pmSel = editor._tiptapEditor.state.selection;
        const parent = pmSel.$from?.parent;
        if (parent?.type?.name === 'paragraph' && parent?.content?.size === 0) {
          const selDOM = window.getSelection();
          if (selDOM?.rangeCount && selDOM.rangeCount > 0) {
            const range = selDOM.getRangeAt(0);
            if (!range.collapsed) {
              e.preventDefault();
              e.stopPropagation();
              selDOM.removeAllRanges();
              const newRange = document.createRange();
              newRange.setStart(range.startContainer, 0);
              newRange.collapse(true);
              selDOM.addRange(newRange);
              return;
            }
          }
        }
      }

    };
    document.addEventListener('keydown', handler, { capture: true });

    return () => {
      document.removeEventListener('keydown', handler, { capture: true });
    };
  }, [editorRef]);

  useEffect(() => {
    const handleMousedown = (event) => {
      const editor = editorRef.current;
      if (!editor || typeof editor.insertBlocks !== 'function') return;

      const emojiTarget = event.target;
      if (emojiTarget?.closest?.('#bn-grid-suggestion-menu, .bn-formatting-toolbar, .bn-panel, em-emoji-picker')) return;

      const y = event.clientY;

      const BLOCK_SELECTOR = [
        '.bn-block-content[data-content-type="codeBlock"]',
        '.bn-block-content[data-content-type="image"]',
        '.bn-block-content[data-content-type="video"]',
        '.bn-visual-media-wrapper',
      ].join(',');

      const VISUAL_TYPES = ['codeBlock', 'image', 'video'];

      const blocks = document.querySelectorAll(BLOCK_SELECTOR);

      const seen = new Set();

      for (const block of blocks) {
        const outer = block.closest('.bn-block-outer');
        if (!outer) continue;
        const blockId = outer.dataset.id;
        if (!blockId || seen.has(blockId)) continue;
        seen.add(blockId);
        const rect = outer.getBoundingClientRect();
        const isInBottomGap = y > rect.bottom && y < rect.bottom + GAP_SIZE;
        const isInTopGap = y > rect.top - GAP_SIZE && y < rect.top;

        const allBlocks = editor.document;
        const idx = allBlocks.findIndex(b => b.id === blockId);
        const adjacentBlock = allBlocks[idx + (isInBottomGap ? 1 : -1)];
        const placement = isInBottomGap ? 'after' : 'before';

        if (!isInBottomGap && !isInTopGap) continue;

        if (adjacentBlock && adjacentBlock.type === 'paragraph') {
          const isEmptyParagraph = !adjacentBlock.content || adjacentBlock.content.length === 0;
          if (isEmptyParagraph) return;
        }

        const now = Date.now();
        const gapKey = blockId + ':' + placement;
        const reverseKey = adjacentBlock && VISUAL_TYPES.includes(adjacentBlock.type)
          ? adjacentBlock.id + ':' + (isInTopGap ? 'after' : 'before')
          : null;

        const isDuplicate = gapKey === lastInsertedRef.current.key && now - lastInsertedRef.current.time < 300;
        const isReverseDuplicate = reverseKey === lastInsertedRef.current.key && now - lastInsertedRef.current.time < 300;

        if (isDuplicate || isReverseDuplicate) {
          if (isInTopGap) {
            event.preventDefault();
            event.stopPropagation();
          }
          return;
        }

        lastInsertedRef.current = { key: gapKey, time: now };
        event.preventDefault();
        event.stopPropagation();

        setTimeout(() => {
          try {
            editor.insertBlocks(
              [{ type: 'paragraph' }],
              blockId,
              placement,
              false,
            );
          } catch (e) {
            console.error('Failed to insert paragraph:', e);
          }
        }, 0);
        return;
      }
    };

    document.addEventListener('mousedown', handleMousedown, { capture: true });
    return () => {
      document.removeEventListener('mousedown', handleMousedown, {
        capture: true,
      });
    };
  }, [editorRef]);
}
