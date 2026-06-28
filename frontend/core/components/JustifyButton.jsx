import {
  useBlockNoteEditor,
  useComponentsContext,
  useSelectedBlocks,
} from '@blocknote/react';

export default function JustifyButton() {
  const editor = useBlockNoteEditor();
  const Components = useComponentsContext();
  const blocks = useSelectedBlocks();

  if (blocks.filter((b) => b.content !== undefined).length === 0) {
    return null;
  }

  const isSelected = blocks.some(
    (b) => b.props?.textAlignment === 'justify',
  );

  return (
    <Components.FormattingToolbar.Button
      mainTooltip="Align text justify"
      onClick={() => {
        for (const block of blocks) {
          if (block.props?.textAlignment !== undefined) {
            editor.updateBlock(block, {
              props: { textAlignment: 'justify' },
            });
          }
        }
      }}
      isSelected={isSelected}
      icon={
        <svg
          stroke="currentColor"
          fill="currentColor"
          strokeWidth="0"
          viewBox="0 0 24 24"
          height="1em"
          width="1em"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M3 4H21V6H3V4ZM3 19H21V21H3V19ZM3 14H21V16H3V14ZM3 9H21V11H3V9Z" />
        </svg>
      }
    />
  );
}
