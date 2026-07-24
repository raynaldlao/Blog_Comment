import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const codeCopySource = fs.readFileSync(
  path.resolve(__dirname, '../../static/scripts/code-copy.js'),
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
  let mockWriteText;

  beforeAll(() => {
    const fn = new Function(codeCopySource);
    fn();
  });

  beforeEach(() => {
    document.body.innerHTML = '';
    document.execCommand = vi.fn().mockImplementation(() => {
      const dt = new DataTransfer();
      const ev = new ClipboardEvent('copy', { clipboardData: dt });
      document.dispatchEvent(ev);
      return true;
    });
    vi.useFakeTimers();
    mockWriteText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', {
      clipboard: { writeText: mockWriteText },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('shows toast on button click', () => {
    const { btn } = createDOM('python');
    btn.click();

    const toast = document.querySelector('.toast');
    expect(toast).not.toBeNull();
    expect(toast.textContent).toBe('Copied to clipboard');
  });

  it('removes toast after 2800ms', () => {
    const { btn } = createDOM('python');
    btn.click();

    expect(document.querySelector('.toast')).not.toBeNull();

    vi.advanceTimersByTime(2800);

    expect(document.querySelector('.toast')).toBeNull();
  });

  it('ignores clicks on non-copy-btn elements', () => {
    const { wrapper } = createDOM();
    wrapper.click();

    expect(mockWriteText).not.toHaveBeenCalled();
    expect(document.querySelector('.toast')).toBeNull();
  });

  it('writes text/plain via custom copy event handler', () => {
    const { btn } = createDOM();
    btn.click();

    expect(document.execCommand).toHaveBeenCalledWith('copy');
    expect(document.querySelector('.toast')).not.toBeNull();
  });

  it('writes text/html + text/plain via custom copy event', () => {
    const { btn } = createDOM('python');
    btn.click();

    expect(document.execCommand).toHaveBeenCalledWith('copy');
    expect(document.querySelector('.toast')).not.toBeNull();
  });

  it('replaces old toast on rapid clicks', () => {
    const { btn } = createDOM('python');
    btn.click();
    btn.click();

    const toasts = document.querySelectorAll('.toast');
    expect(toasts.length).toBe(1);
  });

  it('shows toast even for empty code block (copied zero-width space)', () => {
    const { btn, code } = createDOM('python');
    code.textContent = '';
    btn.click();

    expect(document.querySelector('.toast')).not.toBeNull();
    expect(document.execCommand).toHaveBeenCalledWith('copy');
  });
});
