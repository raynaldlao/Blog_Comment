import {
  useBlockNoteEditor,
  useComponentsContext,
  getFormattingToolbarItems,
  FileReplaceButton,
  FileDownloadButton,
  FileCaptionButton,
  FileRenameButton,
  FilePreviewButton,
} from '@blocknote/react';

import JustifyButton from './JustifyButton';
import CopyBlockButton from './CopyBlockButton';


const HIDDEN_VIDEO_BUTTONS = [
  FileReplaceButton,
  FileDownloadButton,
  FileCaptionButton,
  FileRenameButton,
  FilePreviewButton,
];

const HIDDEN_IMAGE_BUTTONS = [
  FileDownloadButton,
];

export function filterVideoToolbarItems(items, hiddenTypes) {
  const hide = hiddenTypes || HIDDEN_VIDEO_BUTTONS;
  return items.filter((item) => {
    if (hide.includes(item.type)) return false;
    if (item.props?.textAlignment) return false;
    return true;
  });
}

export function filterImageToolbarItems(items, hiddenTypes) {
  const hide = hiddenTypes || HIDDEN_IMAGE_BUTTONS;
  return items.filter((item) => {
    if (hide.includes(item.type)) return false;
    return true;
  });
}

function useIsVideo() {
  const editor = useBlockNoteEditor();
  if (!editor) {
    return false;
  }
  try {
    const block = editor.getSelection()?.blocks?.[0]
      ?? editor.getTextCursorPosition().block;
    return block.type === 'video';
  } catch {
    return false;
  }
}

function useIsImage() {
  const editor = useBlockNoteEditor();
  if (!editor) {
    return false;
  }
  try {
    const block = editor.getSelection()?.blocks?.[0]
      ?? editor.getTextCursorPosition().block;
    return block.type === 'image';
  } catch {
    return false;
  }
}

export default function CustomFormattingToolbar() {
  const Components = useComponentsContext();
  if (!Components) {
    return null;
  }

  const isVideo = useIsVideo();
  const isImage = useIsImage();
  const items = getFormattingToolbarItems();

  if (isVideo) {
    const filtered = filterVideoToolbarItems(items);
    return (
      <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
        <CopyBlockButton />
        {filtered}
      </Components.FormattingToolbar.Root>
    );
  }

  if (isImage) {
    const filtered = filterImageToolbarItems(items);
    return (
      <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
        <CopyBlockButton />
        {filtered}
      </Components.FormattingToolbar.Root>
    );
  }

  const rightIdx = items.findIndex(
    (item) => { return item.props?.textAlignment === 'right'; },
  );

  return (
    <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
      {items.slice(0, rightIdx + 1)}
      <JustifyButton />
      {items.slice(rightIdx + 1)}
    </Components.FormattingToolbar.Root>
  );
}
