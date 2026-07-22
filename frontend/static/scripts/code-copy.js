(() => {
  'use strict';

  const DEBUG = false;
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

    const text = codeEl.textContent || '';
    if (!text) return;

    const lang = btn.dataset.lang || '';
    const pre = codeBlock.querySelector('pre');
    const preClone = pre.cloneNode(true);
    if (lang) preClone.dataset.lang = lang;
    const codeClone = preClone.querySelector('code');
    if (lang && codeClone) codeClone.dataset.language = lang;
    const html = preClone.outerHTML || '';

    const doCopy = () => {
      const hasItem = typeof ClipboardItem !== 'undefined';
      if (hasItem && html) {
        return navigator.clipboard.write([
          new ClipboardItem({
            'text/html': new Blob([html], { type: 'text/html' }),
            'text/plain': new Blob([text], { type: 'text/plain' }),
          }),
        ]);
      }
      return navigator.clipboard.writeText(text);
    };

    doCopy().catch(() => {
      if (DEBUG) console.error('Copy failed');
    });

    const oldToast = document.querySelector('.toast');
    if (oldToast) oldToast.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = _t('Copied to clipboard');

    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 2800);
  });
})();
