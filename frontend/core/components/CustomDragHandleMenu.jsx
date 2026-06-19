import { SideMenuExtension } from '@blocknote/core/extensions';
import {
  DragHandleMenu,
  BlockColorsItem,
  RemoveBlockItem,
  useExtensionState,
} from '@blocknote/react';

function CustomDragHandleMenu() {
  const block = useExtensionState(SideMenuExtension, {
    selector: (state) => state?.block,
  });
  const isImageOrVideo = block?.type === 'image' || block?.type === 'video';

  return (
    <DragHandleMenu>
      <RemoveBlockItem>Delete</RemoveBlockItem>
      {!isImageOrVideo && <BlockColorsItem>Colors</BlockColorsItem>}
    </DragHandleMenu>
  );
}

export default CustomDragHandleMenu;
