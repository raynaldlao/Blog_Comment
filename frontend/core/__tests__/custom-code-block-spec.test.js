import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createCustomCodeBlockSpec } from '../utils/custom-code-block-spec';
import { withBlockSelection, resetBlockSelection } from '../utils/with-block-selection';

const mockRender = vi.fn();
const mockSpec = {
  implementation: {
    render: mockRender,
  },
};

vi.mock('@blocknote/core', () => ({
  createCodeBlockSpec: vi.fn(() => mockSpec),
}));

function createMockBlock(id, lang, type) {
  const block = { id };
  if (type) block.type = type;
  if (lang) block.props = { language: lang };
  return block;
}

function createMockViewerDom(lang) {
  const outerDiv = document.createElement('div');
  const pre = document.createElement('pre');
  const code = document.createElement('code');
  code.textContent = 'print("hello")';
  if (lang) code.classList.add('language-' + lang);
  pre.appendChild(code);
  outerDiv.appendChild(pre);
  return outerDiv;
}

function createMockEditor(isEditable) {
  const removeBlocks = vi.fn();
  const listeners = [];
  const getTextCursorPosition = vi.fn(() => undefined);
  const onSelectionChange = vi.fn((cb) => {
    listeners.push(cb);
    return () => {
      const idx = listeners.indexOf(cb);
      if (idx >= 0) listeners.splice(idx, 1);
    };
  });
  const focus = vi.fn();
  const blur = vi.fn();
  const setTextCursorPosition = vi.fn();
  const updateBlock = vi.fn();
  const undo = vi.fn();
  const redo = vi.fn();
  return { isEditable, removeBlocks, onSelectionChange, getTextCursorPosition, focus, blur, setTextCursorPosition, updateBlock, undo, redo, _listeners: listeners, dom: document.createElement('div') };
}

function createMockSelect(options) {
  const select = document.createElement('select');
  options.forEach((opt) => {
    const el = document.createElement('option');
    el.value = opt.value;
    el.textContent = opt.text;
    select.appendChild(el);
  });
  return select;
}

beforeEach(() => {
  document.body.innerHTML = '';
  mockRender.mockReset();
  mockSpec.implementation.render = mockRender;
  vi.restoreAllMocks();
  vi.stubGlobal('requestAnimationFrame', (cb) => { cb(); });
  vi.stubGlobal('cancelAnimationFrame', () => {});
});

afterEach(() => {
  resetBlockSelection();
  document.body.innerHTML = '';
});

function renderSpec() {
  const spec = createCustomCodeBlockSpec({
    defaultLanguage: 'plaintext',
    supportedLanguages: { plaintext: { name: 'Plain Text' }, js: { name: 'JavaScript' }, py: { name: 'Python' } },
    createHighlighter: () => ({}),
  });
  return spec;
}

describe('createCustomCodeBlockSpec', () => {
  it('returns an object with implementation.render', () => {
    const spec = renderSpec();
    expect(spec).toHaveProperty('implementation');
    expect(typeof spec.implementation.render).toBe('function');
  });

  it('creates language selector widget in editable editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });

    spec.implementation.render(block, editor);

    expect(mockRender).toHaveBeenCalled();
    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    expect(trigger).not.toBeNull();
  });

  it('creates static lang label in non-editable viewer', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(false);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });

    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    expect(trigger).not.toBeNull();
    expect(trigger.textContent).toBe('Plain Text');
  });

  it('opens and closes dropdown on trigger click', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    expect(dropdown).not.toBeNull();
    expect(dropdown.classList.contains('code-block-lang-dropdown--open')).toBe(true);

    trigger.click();

    expect(dropdown.classList.contains('code-block-lang-dropdown--open')).toBe(false);
  });

  it('closes dropdown on outside click', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    expect(dropdown.classList.contains('code-block-lang-dropdown--open')).toBe(true);

    document.body.click();

    expect(dropdown.classList.contains('code-block-lang-dropdown--open')).toBe(false);
  });

  it('filters languages by search input', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
      { value: 'py', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    const searchInput = dropdown.querySelector('.code-block-lang-search');
    const items = dropdown.querySelectorAll('.code-block-lang-item');

    searchInput.value = 'pyt';
    searchInput.dispatchEvent(new Event('input'));

    expect(items[0].style.display).toBe('none');
    expect(items[1].style.display).toBe('none');
    expect(items[2].style.display).not.toBe('none');
  });

  it('selects language on item click', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    const items = dropdown.querySelectorAll('.code-block-lang-item');

    items[1].click();

    expect(select.value).toBe('js');
  });

  it('adds copy button in editable editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const btn = outerDiv.querySelector('.code-copy-btn');
    expect(btn).not.toBeNull();
    const svg = btn.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg.getAttribute('viewBox')).toBe('0 0 24 24');
  });

  it('adds copy button in non-editable viewer', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(false);

    const outerDiv = createMockViewerDom();
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const btn = outerDiv.querySelector('.code-copy-btn');
    expect(btn).not.toBeNull();
    const svg = btn.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg.getAttribute('viewBox')).toBe('0 0 24 24');
  });

  it('sets data-lang on copy button from DOM code class', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(false);

    const outerDiv = createMockViewerDom('python');
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const btn = outerDiv.querySelector('.code-copy-btn');
    expect(btn.dataset.lang).toBe('python');
  });

  it('sets no data-lang when DOM has no language', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(false);

    const outerDiv = createMockViewerDom();
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const btn = outerDiv.querySelector('.code-copy-btn');
    expect(btn.dataset.lang).toBeUndefined();
  });

  it('does not duplicate copy button on re-render', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(false);

    const outerDiv = createMockViewerDom();
    mockRender.mockReturnValue({ dom: outerDiv });

    spec.implementation.render(block, editor);
    spec.implementation.render(block, editor);

    const btns = outerDiv.querySelectorAll('.code-copy-btn');
    expect(btns.length).toBe(1);
  });

  it('shows tooltip on copy button mouseenter', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const copyBtn = outerDiv.querySelector('.code-copy-btn');
    copyBtn.dispatchEvent(new MouseEvent('mouseenter'));

    const tooltip = document.querySelector('.code-block-tooltip');
    expect(tooltip).not.toBeNull();
    expect(tooltip.textContent).toBe('Copy');
  });

  it('removes tooltip on copy button mouseleave', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const copyBtn = outerDiv.querySelector('.code-copy-btn');
    copyBtn.dispatchEvent(new MouseEvent('mouseenter'));
    copyBtn.dispatchEvent(new MouseEvent('mouseleave'));

    const tooltip = document.querySelector('.code-block-tooltip');
    expect(tooltip).toBeNull();
  });

  it('closes dropdown on Escape key', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    const searchInput = dropdown.querySelector('.code-block-lang-search');

    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));

    expect(dropdown.classList.contains('code-block-lang-dropdown--open')).toBe(false);
  });

  it('sets data-lang on copy button from select value in editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    select.value = 'python';
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const btn = outerDiv.querySelector('.code-copy-btn');
    expect(btn.dataset.lang).toBe('python');
  });

  it('navigates dropdown items with ArrowDown', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
      { value: 'py', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    const searchInput = dropdown.querySelector('.code-block-lang-search');
    const items = dropdown.querySelectorAll('.code-block-lang-item');

    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));

    expect(items[0].classList.contains('code-block-lang-item--focused')).toBe(true);

    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));

    expect(items[1].classList.contains('code-block-lang-item--focused')).toBe(true);
  });

  it('navigates dropdown items with ArrowUp and wraps to last', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
      { value: 'py', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    const searchInput = dropdown.querySelector('.code-block-lang-search');
    const items = dropdown.querySelectorAll('.code-block-lang-item');

    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true }));

    expect(items[2].classList.contains('code-block-lang-item--focused')).toBe(true);
  });

  it('selects language on Enter when item is focused', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'plaintext', text: 'Plain Text' },
      { value: 'js', text: 'JavaScript' },
      { value: 'py', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const trigger = outerDiv.querySelector('.code-block-lang-trigger');
    trigger.click();

    const dropdown = document.querySelector('.code-block-lang-dropdown');
    const searchInput = dropdown.querySelector('.code-block-lang-search');

    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));

    expect(select.value).toBe('js');
  });

  it('shows delete button in editable editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const deleteBtn = outerDiv.querySelector('.code-delete-btn');
    expect(deleteBtn).not.toBeNull();
    const svg = deleteBtn.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg.getAttribute('viewBox')).toBe('0 0 24 24');
  });

  it('shows tooltip on delete button mouseenter', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const deleteBtn = outerDiv.querySelector('.code-delete-btn');
    deleteBtn.dispatchEvent(new MouseEvent('mouseenter'));

    const tooltip = document.querySelector('.code-block-tooltip');
    expect(tooltip).not.toBeNull();
    expect(tooltip.textContent).toBe('Delete');
  });

  it('removes tooltip on delete button mouseleave', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const deleteBtn = outerDiv.querySelector('.code-delete-btn');
    deleteBtn.dispatchEvent(new MouseEvent('mouseenter'));
    deleteBtn.dispatchEvent(new MouseEvent('mouseleave'));

    const tooltip = document.querySelector('.code-block-tooltip');
    expect(tooltip).toBeNull();
  });

  it('hides delete button in non-editable viewer', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(false);

    const outerDiv = createMockViewerDom();
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const deleteBtn = outerDiv.querySelector('.code-delete-btn');
    expect(deleteBtn).toBeNull();
  });

  it('creates external selection overlay on document.body', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeTruthy();
    expect(overlay.style.display).toBe('none');

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    expect(overlay.style.display).toBe('block');
  });

  it('hides external selection overlay when selection moves elsewhere', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeTruthy();

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());
    expect(overlay.style.display).toBe('block');

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'other-block' } });
    editor._listeners.forEach((cb) => cb());
    expect(overlay.style.display).toBe('none');
  });

  it('hides external selection overlay when clicking outside editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeTruthy();

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());
    expect(overlay.style.display).toBe('block');

    document.body.dispatchEvent(new Event('click', { bubbles: true }));
    expect(overlay.style.display).toBe('none');
  });

  it('does not create external selection overlay in non-editable mode', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(false);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeNull();
  });

  it('keeps external selection overlay visible when clicking inside editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const pmRoot = document.createElement('div');
    pmRoot.className = 'ProseMirror';
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    pmRoot.appendChild(outerDiv);
    document.body.appendChild(pmRoot);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeTruthy();

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());
    expect(overlay.style.display).toBe('block');

    pmRoot.dispatchEvent(new Event('click', { bubbles: true }));
    expect(overlay.style.display).toBe('block');
  });

  it('calls editor.removeBlocks on delete click', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const deleteBtn = outerDiv.querySelector('.code-delete-btn');
    deleteBtn.click();

    expect(editor.removeBlocks).toHaveBeenCalledTimes(1);
    expect(editor.removeBlocks).toHaveBeenCalledWith([block]);
  });

  it('deletes code block on Backspace when overlay active', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Backspace', bubbles: true }));

    expect(editor.removeBlocks).toHaveBeenCalledTimes(1);
    expect(editor.removeBlocks).toHaveBeenCalledWith([block]);
  });

  it('does not delete code block on Backspace when overlay not active', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Backspace', bubbles: true }));

    expect(editor.removeBlocks).not.toHaveBeenCalled();
  });

  it('enters editing mode on double click', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay.classList.contains('code-block-selection-overlay--editing')).toBe(false);

    document.body.appendChild(outerDiv);
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(overlay.classList.contains('code-block-selection-overlay--editing')).toBe(true);
  });

  it('exits editing mode when switching to non-code block', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    document.body.appendChild(outerDiv);
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(overlay.classList.contains('code-block-selection-overlay--editing')).toBe(true);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'other-block' } });
    editor._listeners.forEach((cb) => cb());
    expect(overlay.classList.contains('code-block-selection-overlay--editing')).toBe(false);
  });

  it('does not delete code block on Backspace when in editing mode', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    document.body.appendChild(outerDiv);
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Backspace', bubbles: true }));
    expect(editor.removeBlocks).not.toHaveBeenCalled();
  });

  it('shows overlay on selection change when cursor is in code block', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay.style.display).toBe('none');

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    expect(overlay.style.display).toBe('block');
  });

  it('calls editor.undo on Ctrl+Z keydown', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, bubbles: true }));

    expect(editor.undo).toHaveBeenCalledTimes(1);
  });

  it('calls editor.redo on Ctrl+Y keydown', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'y', ctrlKey: true, bubbles: true }));

    expect(editor.redo).toHaveBeenCalledTimes(1);
  });

  it('resets double-click timer when selection is cleared outside editor', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    document.body.appendChild(outerDiv);
    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(overlay.style.display).toBe('block');

    document.body.dispatchEvent(new Event('click', { bubbles: true }));
    expect(overlay.style.display).toBe('none');

    outerDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(overlay.classList.contains('code-block-selection-overlay--editing')).toBe(false);
    expect(overlay.style.display).toBe('block');
  });

  it('clears block selection on Ctrl+A when overlay active', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);

    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([
      { value: 'python', text: 'Python' },
    ]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    const overlay = document.querySelector('.code-block-selection-overlay--external');

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    expect(overlay.style.display).toBe('block');

    document.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'a', ctrlKey: true, bubbles: true,
    }));

    expect(overlay.style.display).toBe('none');
  });

  it('calls editor.redo on Ctrl+Shift+Z keydown', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, shiftKey: true, bubbles: true }));

    expect(editor.redo).toHaveBeenCalledTimes(1);
  });

  it('registers image block in blockIdMap without creating overlay', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', undefined, 'image');
    const editor = createMockEditor(true);
    const bnBlockContent = document.createElement('div');
    bnBlockContent.className = 'bn-block-content';
    bnBlockContent.setAttribute('data-content-type', 'image');
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    bnBlockContent.appendChild(outerDiv);
    document.body.appendChild(bnBlockContent);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    // No overlay for image blocks
    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeNull();

    // Selecting image block should not create overlay
    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    const overlayAfter = document.querySelector('.code-block-selection-overlay--external');
    expect(overlayAfter).toBeNull();
  });

  it('does not crash on image block copy when node-selected', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1');
    const editor = createMockEditor(true);

    const bnBlockContent = document.createElement('div');
    bnBlockContent.className = 'bn-block-content';
    bnBlockContent.setAttribute('data-content-type', 'image');
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    bnBlockContent.appendChild(outerDiv);
    document.body.appendChild(bnBlockContent);

    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    // Select the image block via node selection path
    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    // Ctrl+C on image should not throw
    expect(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'c', ctrlKey: true, bubbles: true }));
    }).not.toThrow();
  });

  it('toggles .ProseMirror-selectednode on video mousedown and outside click', () => {
    const spec = renderSpec();
    const editor = createMockEditor(true);

    // Register code block first to trigger initListeners (mousedownHandler, clickHandler)
    const codeBlock = createMockBlock('code-1', 'python', 'codeBlock');
    const codeOuterDiv = document.createElement('div');
    const codeWrapperDiv = document.createElement('div');
    codeWrapperDiv.setAttribute('contenteditable', 'false');
    codeOuterDiv.appendChild(codeWrapperDiv);
    document.body.appendChild(codeOuterDiv);
    mockRender.mockReturnValueOnce({ dom: codeOuterDiv });
    spec.implementation.render(codeBlock, editor);

    // Register video block
    const videoBlock = createMockBlock('vid-1', undefined, 'video');
    const bnBlockContent = document.createElement('div');
    bnBlockContent.className = 'bn-block-content';
    bnBlockContent.setAttribute('data-content-type', 'video');
    const videoOuterDiv = document.createElement('div');
    const mediaWrapper = document.createElement('div');
    mediaWrapper.className = 'bn-visual-media-wrapper';
    mediaWrapper.appendChild(document.createElement('iframe'));
    videoOuterDiv.appendChild(mediaWrapper);
    bnBlockContent.appendChild(videoOuterDiv);
    document.body.appendChild(bnBlockContent);
    mockRender.mockReturnValueOnce({ dom: videoOuterDiv });
    spec.implementation.render(videoBlock, editor);

    // First mousedown → class added
    bnBlockContent.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(bnBlockContent.classList.contains('ProseMirror-selectednode')).toBe(true);

    // Outside click → class removed
    const outsideEl = document.createElement('div');
    document.body.appendChild(outsideEl);
    outsideEl.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    expect(bnBlockContent.classList.contains('ProseMirror-selectednode')).toBe(false);

    // Second mousedown → class added again
    bnBlockContent.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(bnBlockContent.classList.contains('ProseMirror-selectednode')).toBe(true);
  });

  it('adds .ProseMirror-selectednode on block-content not media-wrapper', () => {
    const spec = renderSpec();
    const editor = createMockEditor(true);

    const codeBlock = createMockBlock('code-1', 'python', 'codeBlock');
    const codeOuterDiv = document.createElement('div');
    const codeWrapperDiv = document.createElement('div');
    codeWrapperDiv.setAttribute('contenteditable', 'false');
    codeOuterDiv.appendChild(codeWrapperDiv);
    document.body.appendChild(codeOuterDiv);
    mockRender.mockReturnValueOnce({ dom: codeOuterDiv });
    spec.implementation.render(codeBlock, editor);

    const videoBlock = createMockBlock('vid-2', undefined, 'video');
    const bnBlockContent = document.createElement('div');
    bnBlockContent.className = 'bn-block-content';
    bnBlockContent.setAttribute('data-content-type', 'video');
    const videoOuterDiv = document.createElement('div');
    const mediaWrapper = document.createElement('div');
    mediaWrapper.className = 'bn-visual-media-wrapper';
    mediaWrapper.appendChild(document.createElement('iframe'));
    videoOuterDiv.appendChild(mediaWrapper);
    bnBlockContent.appendChild(videoOuterDiv);
    document.body.appendChild(bnBlockContent);
    mockRender.mockReturnValueOnce({ dom: videoOuterDiv });
    spec.implementation.render(videoBlock, editor);

    bnBlockContent.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));

    expect(bnBlockContent.classList.contains('ProseMirror-selectednode')).toBe(true);
    expect(mediaWrapper.classList.contains('ProseMirror-selectednode')).toBe(false);
  });

  it('cleans .ProseMirror-selectednode from video when clicking paragraph block', () => {
    const spec = renderSpec();
    const editor = createMockEditor(true);

    // 1st code block to trigger initListeners
    const code1 = createMockBlock('code-1', 'python', 'codeBlock');
    const code1Outer = document.createElement('div');
    code1Outer.appendChild(document.createElement('div'));
    document.body.appendChild(code1Outer);
    mockRender.mockReturnValueOnce({ dom: code1Outer });
    spec.implementation.render(code1, editor);

    // Video block
    const vidBlock = createMockBlock('vid-1', undefined, 'video');
    const bnBlockContent = document.createElement('div');
    bnBlockContent.className = 'bn-block-content';
    bnBlockContent.setAttribute('data-content-type', 'video');
    const vidOuterDiv = document.createElement('div');
    const mediaWrapper = document.createElement('div');
    mediaWrapper.className = 'bn-visual-media-wrapper';
    mediaWrapper.appendChild(document.createElement('iframe'));
    vidOuterDiv.appendChild(mediaWrapper);
    bnBlockContent.appendChild(vidOuterDiv);
    document.body.appendChild(bnBlockContent);
    mockRender.mockReturnValueOnce({ dom: vidOuterDiv });
    spec.implementation.render(vidBlock, editor);

    // 2nd code block as paragraph target
    const code2 = createMockBlock('code-2', 'python', 'codeBlock');
    const code2Outer = document.createElement('div');
    const code2Wrapper = document.createElement('div');
    code2Wrapper.setAttribute('contenteditable', 'false');
    code2Outer.appendChild(code2Wrapper);
    document.body.appendChild(code2Outer);
    mockRender.mockReturnValueOnce({ dom: code2Outer });
    spec.implementation.render(code2, editor);

    // Click video → .ProseMirror-selectednode added
    bnBlockContent.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(bnBlockContent.classList.contains('ProseMirror-selectednode')).toBe(true);

    // Click paragraph → class cleaned from video, overlay shown on paragraph
    code2Outer.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    expect(bnBlockContent.classList.contains('ProseMirror-selectednode')).toBe(false);

    const overlay = document.querySelector('.code-block-selection-overlay--external');
    expect(overlay).toBeTruthy();
    expect(overlay.style.display).toBe('block');
    expect(code2Outer.classList.contains('block-selected')).toBe(true);
  });

  it('copies code block on Ctrl+C and pastes with type conversion', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python', 'codeBlock');
    const editor = createMockEditor(true);
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'c', ctrlKey: true, bubbles: true }));

    const pasteEvent = new Event('paste', { bubbles: true, cancelable: true });
    pasteEvent.preventDefault = vi.fn();
    pasteEvent.stopPropagation = vi.fn();
    document.dispatchEvent(pasteEvent);

    expect(editor.updateBlock).toHaveBeenCalledTimes(1);
    expect(editor.updateBlock).toHaveBeenCalledWith(
      block,
      expect.objectContaining({ type: 'codeBlock' })
    );
    expect(editor.blur).toHaveBeenCalled();
  });

  it('pastes clipboard text as paragraph when no copy buffer', () => {
    const spec = renderSpec();
    const block = createMockBlock('block-1', 'python');
    const editor = createMockEditor(true);
    const outerDiv = document.createElement('div');
    const wrapperDiv = document.createElement('div');
    wrapperDiv.setAttribute('contenteditable', 'false');
    const select = createMockSelect([{ value: 'python', text: 'Python' }]);
    wrapperDiv.appendChild(select);
    outerDiv.appendChild(wrapperDiv);
    mockRender.mockReturnValue({ dom: outerDiv });
    spec.implementation.render(block, editor);

    editor.getTextCursorPosition.mockReturnValue({ block: { id: 'block-1' } });
    editor._listeners.forEach((cb) => cb());

    const pasteEvent = new Event('paste', { bubbles: true, cancelable: true });
    pasteEvent.preventDefault = vi.fn();
    pasteEvent.stopPropagation = vi.fn();
    Object.defineProperty(pasteEvent, 'clipboardData', {
      value: { getData: vi.fn(() => 'hello world') },
    });
    document.dispatchEvent(pasteEvent);

    expect(editor.updateBlock).toHaveBeenCalledWith(
      block,
      expect.objectContaining({ type: 'paragraph', content: 'hello world' })
    );
  });
});
