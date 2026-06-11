import { describe, it, expect, vi, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
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
  const wrapper = document.createElement('div');
  wrapper.className = 'code-block-wrapper';
  const pre = document.createElement('pre');
  const code = document.createElement('code');
  code.textContent = 'print("hello")';
  if (lang) code.classList.add('language-' + lang);
  pre.appendChild(code);
  wrapper.appendChild(pre);

  const btn = document.createElement('button');
  btn.className = 'code-copy-btn';
  btn.textContent = 'Copy';
  if (lang) btn.dataset.lang = lang;
  wrapper.appendChild(btn);

  document.body.appendChild(wrapper);
  return { wrapper, btn, pre, code };
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

  it('shows Copied feedback on button click', () => {
    const { btn } = createDOM('python');
    btn.click();

    expect(btn.textContent).toBe('Copied !');
    expect(btn.classList.contains('copied')).toBe(true);
  });

  it('resets button text after 2000ms', () => {
    const { btn } = createDOM('python');
    btn.click();

    expect(btn.textContent).toBe('Copied !');

    vi.advanceTimersByTime(2000);

    expect(btn.textContent).toBe('Copy');
    expect(btn.classList.contains('copied')).toBe(false);
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
});
