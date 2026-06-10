(() => {
  'use strict';

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.code-copy-btn');
    if (!btn) return;

    const wrapper = btn.closest('.code-block-wrapper');
    const codeEl = wrapper?.querySelector('pre code');
    if (!codeEl) return;

    const text = codeEl.textContent || '';
    if (!text) return;

    const lang = btn.dataset.lang || '';
    const pre = wrapper.querySelector('pre');
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

    const original = btn.textContent;
    btn.textContent = 'Copied !';
    btn.classList.add('copied');

    doCopy().catch(() => {
      btn.textContent = 'Failed';
    });

    setTimeout(() => {
      btn.textContent = original;
      btn.classList.remove('copied');
    }, 2000);
  });
})();
