'use strict';

(() => {
    let lastTap = 0;
    const input = document.querySelector('.search-input');
    if (input) {
        input.addEventListener('click', () => {
            const now = Date.now();
            if (lastTap && now - lastTap < 400) {
                input.select();
                lastTap = 0;
            } else {
                lastTap = now;
            }
        });
    }
})();
