"use strict";

(() => {
    const CONFIRM_DIALOG_ID = "confirm-dialog";
    const CONFIRM_MESSAGE_ID = "confirm-message";
    const CONFIRM_YES_ID = "confirm-yes-btn";
    const CONFIRM_CANCEL_ID = "confirm-cancel-btn";

    document.addEventListener("DOMContentLoaded", () => {
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

        document.addEventListener("click", (e) => {
            const trigger = e.target.closest(".confirm-trigger");
            if (!trigger) return;

            lastFocusedElement = trigger;
            targetFormId = trigger.dataset.formId;
            messageEl.textContent = trigger.dataset.confirmMessage;
            dialog.showModal();
            cancelBtn.focus();
        });

        confirmBtn.addEventListener("click", () => {
            if (targetFormId) {
                const form = document.getElementById(targetFormId);
                if (form) form.requestSubmit();
            }
            dialog.close();
        });

        cancelBtn.addEventListener("click", close);

        dialog.addEventListener("click", (e) => {
            if (e.target === dialog) close();
        });

        dialog.addEventListener("keydown", (e) => {
            if (e.key === "Escape") close();
        });
    });
})();
