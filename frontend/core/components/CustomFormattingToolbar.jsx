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


var HIDDEN_VIDEO_BUTTONS = [
  FileReplaceButton,
  FileDownloadButton,
  FileCaptionButton,
  FileRenameButton,
  FilePreviewButton,
];

var HIDDEN_IMAGE_BUTTONS = [
  FileDownloadButton,
];

export function filterVideoToolbarItems(items, hiddenTypes) {
  var hide = hiddenTypes || HIDDEN_VIDEO_BUTTONS;
  return items.filter(function (item) {
    if (hide.includes(item.type)) return false;
    if (item.props?.textAlignment) return false;
    return true;
  });
}

export function filterImageToolbarItems(items, hiddenTypes) {
  var hide = hiddenTypes || HIDDEN_IMAGE_BUTTONS;
  return items.filter(function (item) {
    if (hide.includes(item.type)) return false;
    return true;
  });
}

function useIsVideo() {
  var editor = useBlockNoteEditor();
  if (!editor) {
    return false;
  }
  try {
    var block = editor.getSelection()?.blocks?.[0]
      ?? editor.getTextCursorPosition().block;
    return block.type === 'video';
  } catch {
    return false;
  }
}

function useIsImage() {
  var editor = useBlockNoteEditor();
  if (!editor) {
    return false;
  }
  try {
    var block = editor.getSelection()?.blocks?.[0]
      ?? editor.getTextCursorPosition().block;
    return block.type === 'image';
  } catch {
    return false;
  }
}

export default function CustomFormattingToolbar() {
  var Components = useComponentsContext();
  if (!Components) {
    return null;
  }

  var isVideo = useIsVideo();
  var isImage = useIsImage();
  var items = getFormattingToolbarItems();

  if (isVideo) {
    var filtered = filterVideoToolbarItems(items);
    return (
      <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
        <CopyBlockButton />
        {filtered}
      </Components.FormattingToolbar.Root>
    );
  }

  if (isImage) {
    var filtered = filterImageToolbarItems(items);
    return (
      <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
        <CopyBlockButton />
        {filtered}
      </Components.FormattingToolbar.Root>
    );
  }

  var rightIdx = items.findIndex(
    function (item) { return item.props?.textAlignment === 'right'; },
  );

  return (
    <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
      {items.slice(0, rightIdx + 1)}
      <JustifyButton />
      {items.slice(rightIdx + 1)}
    </Components.FormattingToolbar.Root>
  );
}
