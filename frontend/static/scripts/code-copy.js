(() => {
  'use strict';

  const _t = key => {
    const el = document.getElementById('app-translations');
    if (!el) return key;
    try { return JSON.parse(el.textContent)[key] || key; } catch { return key; }
  };

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.code-copy-btn');
    if (!btn) return;

    const codeBlock = btn.closest('[data-content-type="codeBlock"]');
    const codeEl = codeBlock?.querySelector('pre code');
    if (!codeEl) return;

    const text = (codeEl.textContent || '').replace(/\n$/, '') || '\u200B';

    const lang = btn.dataset.lang || '';
    const pre = codeBlock.querySelector('pre');
    if (!pre) return;
    const preClone = pre.cloneNode(true);
    if (lang) preClone.dataset.lang = lang;
    const codeClone = preClone.querySelector('code');
    if (lang && codeClone) codeClone.dataset.language = lang;
    const html = (preClone.outerHTML || '').replace(/<br class="ProseMirror-trailingBreak">/g, '\u200B');

    const bnContent = text === '\u200B' ? [] : [{ type: 'text', text: text, styles: {} }];
    const bnData = { type: 'codeBlock', props: { language: lang || 'plaintext' }, content: bnContent };
    const bnHtml = '<blocknote-block data-json=\'' + JSON.stringify(bnData).replace(/'/g, '&apos;') + '\'></blocknote-block>';
    const combinedHtml = bnHtml + html;

    const handler = (e) => {
      e.clipboardData.setData('text/html', combinedHtml);
      e.clipboardData.setData('text/plain', text);
      e.preventDefault();
    };
    document.addEventListener('copy', handler);
    const copyOk = document.execCommand('copy');
    document.removeEventListener('copy', handler);

    const oldToast = document.querySelector('.toast');
    if (oldToast) oldToast.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = copyOk ? _t('Copied to clipboard') : _t('Failed to copy');

    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 2800);
  });
})();
