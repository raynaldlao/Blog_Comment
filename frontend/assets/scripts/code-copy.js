(() => {
  'use strict';

  const DEBUG = false;

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

    const oldTip = document.querySelector('.code-copy-tooltip');
    if (oldTip) oldTip.remove();

    const tooltip = document.createElement('div');
    tooltip.className = 'code-copy-tooltip';
    tooltip.textContent = 'Copied to clipboard';

    const rect = btn.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.bottom = (window.innerHeight - rect.top + 6) + 'px';

    document.body.appendChild(tooltip);

    setTimeout(() => {
      if (tooltip.parentElement) tooltip.remove();
    }, 1500);
  });
})();
