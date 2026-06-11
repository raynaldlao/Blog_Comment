import { useEffect, useRef } from 'react';

const GAP_SIZE = 12;

export default function useCodeBlockGapClick(editorRef) {
  const insertedGapsRef = useRef(new Set());
  
  useEffect(() => {
    const handleMousedown = (event) => {
      const editor = editorRef.current;
      if (!editor || typeof editor.insertBlocks !== 'function') return;

      const y = event.clientY;

      const codeBlocks = document.querySelectorAll(
        '.bn-block-content[data-content-type="codeBlock"]',
      );

      for (const block of codeBlocks) {
        const outer = block.closest('.bn-block-outer');
        if (!outer) continue;
        const rect = outer.getBoundingClientRect();
        const isInBottomGap = y > rect.bottom && y < rect.bottom + GAP_SIZE;
        const isInTopGap = y > rect.top - GAP_SIZE && y < rect.top;

        if (isInBottomGap || isInTopGap) {
          const blockEl = block.closest('[data-id]');
          if (!blockEl?.dataset.id) continue;
          const blockId = blockEl.dataset.id;
          const placement = isInBottomGap ? 'after' : 'before';

          const allBlocks = editor.document;
          const idx = allBlocks.findIndex(b => b.id === blockId);
          const adjacentBlock = allBlocks[idx + (isInBottomGap ? 1 : -1)];

          if (adjacentBlock && adjacentBlock.type === 'paragraph' && isInBottomGap) {
            return;
          }

          const gapKey = `${blockId}:${placement}`;
          if (insertedGapsRef.current.has(gapKey)) {
            if (isInTopGap) {
              event.preventDefault();
              event.stopPropagation();
            }
            return;
          }

          insertedGapsRef.current.add(gapKey);
          event.preventDefault();
          event.stopPropagation();

          setTimeout(() => {
            try {
              editor.insertBlocks(
                [{ type: 'paragraph' }],
                blockId,
                placement,
              );
              if (adjacentBlock && adjacentBlock.type === 'codeBlock') {
                const reverseKey = `${adjacentBlock.id}:${isInTopGap ? 'after' : 'before'}`;
                insertedGapsRef.current.add(reverseKey);
              }
              editor.focus();
            } catch (e) {
              console.error('Failed to insert paragraph:', e);
            }
          }, 0);
          return;
        }
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
