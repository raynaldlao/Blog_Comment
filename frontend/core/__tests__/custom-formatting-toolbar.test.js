import { describe, it, expect } from 'vitest';

import { filterVideoToolbarItems, filterImageToolbarItems } from '../components/CustomFormattingToolbar';

const MockReplace = () => {};
const MockDownload = () => {};
const MockCaption = () => {};
const MockRename = () => {};
const MockPreview = () => {};
const MockNormal = () => {};

const HIDDEN = [MockReplace, MockDownload, MockCaption, MockRename, MockPreview];


describe('filterVideoToolbarItems', () => {
  it('filters out FileReplaceButton', () => {
    expect(filterVideoToolbarItems([{ type: MockReplace }], HIDDEN)).toEqual([]);
  });

  it('filters out FileDownloadButton', () => {
    expect(filterVideoToolbarItems([{ type: MockDownload }], HIDDEN)).toEqual([]);
  });

  it('filters out FileCaptionButton', () => {
    expect(filterVideoToolbarItems([{ type: MockCaption }], HIDDEN)).toEqual([]);
  });

  it('filters out FileRenameButton', () => {
    expect(filterVideoToolbarItems([{ type: MockRename }], HIDDEN)).toEqual([]);
  });

  it('filters out FilePreviewButton', () => {
    expect(filterVideoToolbarItems([{ type: MockPreview }], HIDDEN)).toEqual([]);
  });

  it('filters out items with textAlignment prop', () => {
    const items = [{ type: MockNormal, props: { textAlignment: 'right' } }];
    expect(filterVideoToolbarItems(items, HIDDEN)).toEqual([]);
  });

  it('keeps normal buttons', () => {
    const items = [{ type: MockNormal, props: {} }, { type: MockNormal }];
    expect(filterVideoToolbarItems(items, HIDDEN)).toHaveLength(2);
  });

  it('filters multiple items together', () => {
    const items = [
      { type: MockNormal },
      { type: MockReplace },
      { type: MockDownload },
      { type: MockCaption },
      { type: MockRename },
      { type: MockPreview },
      { type: MockNormal, props: { textAlignment: 'left' } },
      { type: MockNormal },
    ];
    expect(filterVideoToolbarItems(items, HIDDEN)).toHaveLength(2);
  });

  it('returns empty array for empty input', () => {
    expect(filterVideoToolbarItems([], HIDDEN)).toEqual([]);
  });

  it('uses default hidden types when none provided', () => {
    const MockUnknown = () => {};
    const items = [{ type: MockUnknown }, { type: MockNormal }];
    // default HIDDEN_VIDEO_BUTTONS = real File*Button from @blocknote/react
    // These won't match our mocks, so both items pass
    // This just verifies the fallback doesn't crash
    expect(filterVideoToolbarItems(items).length).toBeGreaterThanOrEqual(2);
  });
});

describe('filterImageToolbarItems', () => {
  it('filters out FileDownloadButton', () => {
    expect(filterImageToolbarItems([{ type: MockDownload }], [MockDownload])).toEqual([]);
  });

  it('keeps normal buttons', () => {
    expect(filterImageToolbarItems([{ type: MockNormal }])).toHaveLength(1);
  });
});
