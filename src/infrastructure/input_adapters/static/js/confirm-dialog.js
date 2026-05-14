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

        const close = () => {
            dialog.close();
            targetFormId = null;
        };

        document.addEventListener("click", (e) => {
            const trigger = e.target.closest(".confirm-trigger");
            if (!trigger) return;

            targetFormId = trigger.dataset.formId;
            messageEl.textContent = trigger.dataset.confirmMessage;
            dialog.showModal();
        });

        confirmBtn.addEventListener("click", () => {
            if (targetFormId) {
                const form = document.getElementById(targetFormId);
                if (form) form.submit();
            }
            dialog.close();
        });

        cancelBtn.addEventListener("click", close);

        dialog.addEventListener("click", (e) => {
            if (e.target === dialog) close();
        });

        dialog.addEventListener("keydown", (e) => {
            if (e.key === "Escape") targetFormId = null;
        });
    });
})();
