import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createCustomCodeBlockSpec } from '../utils/custom-code-block-spec';

const mockRender = vi.fn();
const mockSpec = {
  implementation: {
    render: mockRender,
  },
};

vi.mock('@blocknote/core', () => ({
  createCodeBlockSpec: vi.fn(() => mockSpec),
}));

function createMockBlock(id) {
  return { id };
}

function createMockEditor(isEditable) {
  return { isEditable };
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
});

afterEach(() => {
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

  it('does not create widget in non-editable editor', () => {
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
    expect(trigger).toBeNull();
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
});
