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
      mainTooltip="Justify"
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
    >
      <span
        className="material-symbols-outlined"
        style={{ fontSize: '1.125rem' }}
      >
        format_align_justify
      </span>
    </Components.FormattingToolbar.Button>
  );
}
