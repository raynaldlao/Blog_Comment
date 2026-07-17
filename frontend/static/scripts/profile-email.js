'use strict';
(() => {
    const MODAL_ID = 'email-modal';
    const OPEN_BTN_ID = 'open-email-modal';
    const CANCEL_BTN_ID = 'email-modal-cancel';

    document.addEventListener('DOMContentLoaded', () => {
        const dialog = document.getElementById(MODAL_ID);
        const openBtn = document.getElementById(OPEN_BTN_ID);
        const cancelBtn = document.getElementById(CANCEL_BTN_ID);
        if (!dialog || !openBtn || !cancelBtn) return;

        openBtn.addEventListener('click', () => dialog.showModal());
        cancelBtn.addEventListener('click', () => dialog.close());

        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) dialog.close();
        });
    });
})();
