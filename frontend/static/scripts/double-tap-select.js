'use strict';

(() => {
    if (!(/Chrome/.test(navigator.userAgent) && /(Mobile|Android)/.test(navigator.userAgent))) return;
    let lastTap = { time: 0, target: null, count: 0 };
    document.addEventListener('click', (e) => {
        if (e.detail === 2) return;
        const input = e.target.closest(
            'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"]):not(.article-editor-title), '
            + 'textarea:not(.article-editor-description)'
        );
        if (!input) return;
        const now = Date.now();
        if (lastTap.target === input && now - lastTap.time < 400) {
            if (lastTap.count === 0) {
                const text = input.value;
                let start = input.selectionStart;
                while (start > 0 && /\S/.test(text[start - 1])) start--;
                let end = input.selectionEnd;
                while (end < text.length && /\S/.test(text[end])) end++;
                input.setSelectionRange(start, end);
                lastTap = { time: now, target: input, count: 1 };
            } else {
                input.select();
                lastTap = { time: 0, target: null, count: 0 };
            }
        } else {
            lastTap = { time: now, target: input, count: 0 };
        }
    });
})();
