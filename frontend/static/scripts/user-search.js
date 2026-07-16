"use strict";

(() => {
    const SEARCH_INPUT_ID = 'user-search';
    const TABLE_ROWS_SELECTOR = '.user-table tbody tr';

    document.addEventListener('DOMContentLoaded', () => {
        const input = document.getElementById(SEARCH_INPUT_ID);
        if (!input) return;

        input.addEventListener('input', () => {
            const q = input.value.toLowerCase();
            const rows = document.querySelectorAll(TABLE_ROWS_SELECTOR);

            for (let i = 0; i < rows.length; i++) {
                const username = rows[i].cells[0].textContent.toLowerCase();
                const email = rows[i].cells[1].textContent.toLowerCase();
                rows[i].style.display = (username.includes(q) || email.includes(q)) ? '' : 'none';
            }
        });
    });
})();
