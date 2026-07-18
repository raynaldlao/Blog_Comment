'use strict';

(() => {
    let lastTap = 0;
    document.addEventListener('click', (e) => {
        const input = e.target.closest(
            'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"]):not(.article-editor-title), '
            + 'textarea:not(.article-editor-description)'
        );
        if (!input) return;
        const now = Date.now();
        if (lastTap && now - lastTap < 400) {
            input.select();
            lastTap = 0;
        } else {
            lastTap = now;
        }
    });
})();
