'use strict';

(() => {
    document.addEventListener('submit', (e) => {
        const btn = e.target.querySelector('button[type="submit"]');
        if (!btn || btn.disabled) return;
        btn.disabled = true;
        setTimeout(() => { btn.disabled = false; }, 10000);
    });
})();
