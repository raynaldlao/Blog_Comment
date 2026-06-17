import { describe, it, expect } from 'vitest';

import { filterVideoToolbarItems } from '../components/CustomFormattingToolbar';

var MockReplace = function MockReplace() {};
var MockDownload = function MockDownload() {};
var MockCaption = function MockCaption() {};
var MockRename = function MockRename() {};
var MockPreview = function MockPreview() {};
var MockNormal = function MockNormal() {};

var HIDDEN = [MockReplace, MockDownload, MockCaption, MockRename, MockPreview];


describe('filterVideoToolbarItems', function () {
  it('filters out FileReplaceButton', function () {
    expect(filterVideoToolbarItems([{ type: MockReplace }], HIDDEN)).toEqual([]);
  });

  it('filters out FileDownloadButton', function () {
    expect(filterVideoToolbarItems([{ type: MockDownload }], HIDDEN)).toEqual([]);
  });

  it('filters out FileCaptionButton', function () {
    expect(filterVideoToolbarItems([{ type: MockCaption }], HIDDEN)).toEqual([]);
  });

  it('filters out FileRenameButton', function () {
    expect(filterVideoToolbarItems([{ type: MockRename }], HIDDEN)).toEqual([]);
  });

  it('filters out FilePreviewButton', function () {
    expect(filterVideoToolbarItems([{ type: MockPreview }], HIDDEN)).toEqual([]);
  });

  it('filters out items with textAlignment prop', function () {
    var items = [{ type: MockNormal, props: { textAlignment: 'right' } }];
    expect(filterVideoToolbarItems(items, HIDDEN)).toEqual([]);
  });

  it('keeps normal buttons', function () {
    var items = [{ type: MockNormal, props: {} }, { type: MockNormal }];
    expect(filterVideoToolbarItems(items, HIDDEN)).toHaveLength(2);
  });

  it('filters multiple items together', function () {
    var items = [
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

  it('returns empty array for empty input', function () {
    expect(filterVideoToolbarItems([], HIDDEN)).toEqual([]);
  });

  it('uses default hidden types when none provided', function () {
    var MockUnknown = function MockUnknown() {};
    var items = [{ type: MockUnknown }, { type: MockNormal }];
    // default HIDDEN_VIDEO_BUTTONS = real File*Button from @blocknote/react
    // These won't match our mocks, so both items pass
    // This just verifies the fallback doesn't crash
    expect(filterVideoToolbarItems(items).length).toBeGreaterThanOrEqual(2);
  });
});
