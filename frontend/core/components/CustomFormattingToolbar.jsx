import {
  useComponentsContext,
  getFormattingToolbarItems,
} from '@blocknote/react';

import JustifyButton from './JustifyButton';


export default function CustomFormattingToolbar() {
  const Components = useComponentsContext();
  if (!Components) {
    return null;
  }

  const items = getFormattingToolbarItems();
  const filtered = items.filter(
    (item) => item.key !== 'nestBlockButton' && item.key !== 'unnestBlockButton',
  );
  const rightIdx = filtered.findIndex(
    (item) => item.props?.textAlignment === 'right',
  );

  return (
    <Components.FormattingToolbar.Root className="bn-toolbar bn-formatting-toolbar">
      {filtered.slice(0, rightIdx + 1)}
      <JustifyButton />
      {filtered.slice(rightIdx + 1)}
    </Components.FormattingToolbar.Root>
  );
}
