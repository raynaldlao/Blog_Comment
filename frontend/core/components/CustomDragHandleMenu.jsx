import { SideMenuExtension } from '@blocknote/core/extensions';
import {
  DragHandleMenu,
  RemoveBlockItem,
  useBlockNoteEditor,
  useExtensionState,
} from '@blocknote/react';
import { Menu } from '@mantine/core';
import { _ } from '../utils/i18n';

function CustomDragHandleMenu() {
  const editor = useBlockNoteEditor();
  const block = useExtensionState(SideMenuExtension, {
    selector: (state) => state?.block,
  });

  const moveUp = () => {
    if (!editor || !block) return;
    editor.moveBlocksUp(block.id);
  };

  const moveDown = () => {
    if (!editor || !block) return;
    editor.moveBlocksDown(block.id);
  };

  return (
    <DragHandleMenu>
      <Menu.Item onClick={moveUp}>{_('Move Up')}</Menu.Item>
      <Menu.Item onClick={moveDown}>{_('Move Down')}</Menu.Item>
      <RemoveBlockItem>{_('Delete')}</RemoveBlockItem>
    </DragHandleMenu>
  );
}

export default CustomDragHandleMenu;
