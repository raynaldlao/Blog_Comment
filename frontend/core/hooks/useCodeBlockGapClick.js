import { useEffect, useRef } from 'react';

const GAP_SIZE = 12;

export default function useCodeBlockGapClick(editorRef) {
  const lastInsertedRef = useRef({ key: '', time: 0 });

  useEffect(() => {
    const handleMousedown = (event) => {
      const editor = editorRef.current;
      if (!editor || typeof editor.insertBlocks !== 'function') return;

      const y = event.clientY;

      var BLOCK_SELECTOR = [
        '.bn-block-content[data-content-type="codeBlock"]',
        '.bn-block-content[data-content-type="image"]',
        '.bn-visual-media-wrapper',
      ].join(',');

      var VISUAL_TYPES = ['codeBlock', 'image', 'video'];

      const blocks = document.querySelectorAll(BLOCK_SELECTOR);

      var seen = new Set();

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
            );
            editor.focus();
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
