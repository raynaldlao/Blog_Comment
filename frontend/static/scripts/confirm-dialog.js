'use strict';

(() => {
    const CONFIRM_DIALOG_ID = 'confirm-dialog';
    const CONFIRM_MESSAGE_ID = 'confirm-message';
    const CONFIRM_YES_ID = 'confirm-yes-btn';
    const CONFIRM_CANCEL_ID = 'confirm-cancel-btn';

    document.addEventListener('DOMContentLoaded', () => {
        const dialog = document.getElementById(CONFIRM_DIALOG_ID);
        const messageEl = document.getElementById(CONFIRM_MESSAGE_ID);
        const confirmBtn = document.getElementById(CONFIRM_YES_ID);
        const cancelBtn = document.getElementById(CONFIRM_CANCEL_ID);

        if (!dialog || !messageEl || !confirmBtn || !cancelBtn) return;

        let targetFormId = null;
        let lastFocusedElement = null;

        const close = () => {
            dialog.close();
            targetFormId = null;
            if (lastFocusedElement) {
                lastFocusedElement.focus();
                lastFocusedElement = null;
            }
        };

        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('.confirm-trigger');
            if (!trigger) return;

            e.preventDefault();
            lastFocusedElement = trigger;
            targetFormId = trigger.dataset.formId;
            messageEl.textContent = trigger.dataset.confirmMessage;
            dialog.showModal();
            cancelBtn.focus();
        });

        confirmBtn.addEventListener('click', () => {
            if (targetFormId) {
                const form = document.getElementById(targetFormId);
                if (form) {
                    if (form.requestSubmit) {
                        form.requestSubmit();
                    } else {
                        form.submit();
                    }
                }
            }
            dialog.close();
        });

        cancelBtn.addEventListener('click', close);

        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) close();
        });

        dialog.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') close();
        });
    });

    const BAN_TRIGGER_SELECTOR = '.ban-trigger';

    document.addEventListener('click', (e) => {
        const trigger = e.target.closest(BAN_TRIGGER_SELECTOR);
        if (!trigger) return;

        const userId = trigger.getAttribute('data-user-id');
        const username = trigger.getAttribute('data-username');
        const modal = document.getElementById('ban-modal');
        if (!modal) return;

        const form = document.getElementById('ban-form');
        form.action = '/admin/users/' + userId + '/ban';

        document.getElementById('ban-username').textContent = username;
        document.getElementById('ban-reason-input').value = '';
        document.getElementById('ban-reason-count').textContent = '0';
        modal.showModal();
    });

    document.addEventListener('click', (e) => {
        if (e.target.id === 'ban-modal-cancel') {
            document.getElementById('ban-modal')?.close();
        }
    });

    document.addEventListener('input', (e) => {
        if (e.target.id === 'ban-reason-input') {
            document.getElementById('ban-reason-count').textContent = e.target.value.length;
        }
    });
})();
