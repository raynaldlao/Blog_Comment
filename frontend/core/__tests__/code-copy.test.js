import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const codeCopySource = fs.readFileSync(
  path.resolve(__dirname, '../../assets/scripts/code-copy.js'),
  'utf-8',
);

function createDOM(lang) {
  const codeBlock = document.createElement('div');
  codeBlock.setAttribute('data-content-type', 'codeBlock');
  const pre = document.createElement('pre');
  const code = document.createElement('code');
  code.textContent = 'print("hello")';
  if (lang) code.classList.add('language-' + lang);
  pre.appendChild(code);
  codeBlock.appendChild(pre);

  const btn = document.createElement('button');
  btn.className = 'code-copy-btn';
  btn.textContent = 'Copy';
  if (lang) btn.dataset.lang = lang;
  codeBlock.appendChild(btn);

  document.body.appendChild(codeBlock);
  return { wrapper: codeBlock, btn, pre, code };
}

describe('code-copy.js', () => {
  let mockWrite;
  let mockWriteText;

  beforeAll(() => {
    const fn = new Function(codeCopySource);
    fn();
  });

  beforeEach(() => {
    document.body.innerHTML = '';
    vi.useFakeTimers();
    mockWrite = vi.fn().mockResolvedValue(undefined);
    mockWriteText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', {
      clipboard: { write: mockWrite, writeText: mockWriteText },
    });
    vi.stubGlobal('ClipboardItem', undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('shows tooltip on button click', () => {
    const { btn } = createDOM('python');
    btn.click();

    const tooltip = document.querySelector('.code-copy-tooltip');
    expect(tooltip).not.toBeNull();
    expect(tooltip.textContent).toBe('Copied to clipboard');
  });

  it('removes tooltip after 1500ms', () => {
    const { btn } = createDOM('python');
    btn.click();

    expect(document.querySelector('.code-copy-tooltip')).not.toBeNull();

    vi.advanceTimersByTime(1500);

    expect(document.querySelector('.code-copy-tooltip')).toBeNull();
  });

  it('ignores clicks on non-copy-btn elements', () => {
    const { wrapper } = createDOM();
    wrapper.click();

    expect(mockWriteText).not.toHaveBeenCalled();
  });

  it('writes text/plain via writeText as fallback when ClipboardItem absent', () => {
    const { btn } = createDOM();
    btn.click();

    expect(mockWriteText).toHaveBeenCalledWith('print("hello")');
    expect(mockWrite).not.toHaveBeenCalled();
  });

  it('writes text/html + text/plain via ClipboardItem when available', () => {
    const mockClipboardItem = vi.fn();
    vi.stubGlobal('ClipboardItem', mockClipboardItem);

    const { btn } = createDOM('python');
    btn.click();

    expect(mockClipboardItem).toHaveBeenCalledOnce();
    expect(mockWrite).toHaveBeenCalledOnce();
    expect(mockWriteText).not.toHaveBeenCalled();
  });

  it('replaces old tooltip on rapid clicks', () => {
    const { btn } = createDOM('python');
    btn.click();
    btn.click();

    const tooltips = document.querySelectorAll('.code-copy-tooltip');
    expect(tooltips.length).toBe(1);
  });

  it('does nothing when code block is empty', () => {
    const { btn, code } = createDOM('python');
    code.textContent = '';
    btn.click();

    expect(document.querySelector('.code-copy-tooltip')).toBeNull();
    expect(mockWriteText).not.toHaveBeenCalled();
  });

  it('positions tooltip with pixel values', () => {
    const { btn } = createDOM('python');
    vi.stubGlobal('window', { innerHeight: 900 });
    btn.click();

    const tooltip = document.querySelector('.code-copy-tooltip');
    expect(tooltip.style.left).toMatch(/^\d+px$/);
    expect(tooltip.style.bottom).toMatch(/^\d+px$/);
  });
});
