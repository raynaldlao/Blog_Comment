"use strict";

(() => {
    const TOGGLE_SELECTOR = '.password-toggle';
    const WRAPPER_SELECTOR = '.password-wrapper';

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll(TOGGLE_SELECTOR).forEach((btn) => {
            btn.addEventListener('click', () => {
                const wrapper = btn.closest(WRAPPER_SELECTOR);
                const input = wrapper.querySelector('input');
                const isPassword = input.type === 'password';

                input.type = isPassword ? 'text' : 'password';
                btn.textContent = isPassword ? 'visibility' : 'visibility_off';
                btn.setAttribute('aria-pressed', String(!isPassword));
            });
        });
    });
})();
