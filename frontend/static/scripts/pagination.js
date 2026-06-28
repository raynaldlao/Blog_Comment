"use strict";

(() => {
    const JUMP_MODAL_ID = 'jump-modal';
    const JUMP_PAGE_INPUT_ID = 'jump-page-input';
    const JUMP_EXECUTE_BTN_ID = 'jump-execute-btn';
    const JUMP_CANCEL_BTN_ID = 'jump-cancel-btn';
    const JUMP_TRIGGER_SELECTOR = '.jump-modal-trigger';
    const STEPPER_SELECTOR = '.stepper-btn';
    const INPUT_ERROR_CLASS = 'input-error';

    document.addEventListener('DOMContentLoaded', () => {
        const jumpModal = document.getElementById(JUMP_MODAL_ID);
        if (!jumpModal) return;

        const jumpInput = document.getElementById(JUMP_PAGE_INPUT_ID);
        if (!jumpInput) return;
        const totalPages = parseInt(jumpModal.dataset.totalPages, 10);
        const baseUrl = jumpModal.dataset.url;

        const openJumpModal = () => {
            jumpModal.showModal();
            jumpInput.value = '';
        };

        jumpModal.addEventListener('focus', () => jumpInput.focus(), { once: true });

        jumpInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey || e.altKey) return;
            if (e.key.length > 1) return;

            if (!/^\d$/.test(e.key)) {
                e.preventDefault();
            }
        });

        jumpInput.addEventListener('paste', (e) => {
            const data = e.clipboardData.getData('text');
            if (!/^\d+$/.test(data)) {
                e.preventDefault();
            }
        });

        const closeJumpModal = () => jumpModal.close();

        const executeJump = () => {
            const val = parseInt(jumpInput.value, 10);
            if (val && val >= 1 && val <= totalPages) {
                window.location.href = `${baseUrl}?page=${val}`;
            } else {
                jumpInput.classList.add(INPUT_ERROR_CLASS);
                setTimeout(() => {
                    jumpInput.classList.remove(INPUT_ERROR_CLASS);
                }, 500);
            }
        };

        document.addEventListener('click', (e) => {
            if (e.target.closest(JUMP_TRIGGER_SELECTOR)) {
                openJumpModal();
                return;
            }

            const id = e.target.id;
            if (id === JUMP_EXECUTE_BTN_ID) {
                executeJump();
                return;
            }
            if (id === JUMP_CANCEL_BTN_ID) {
                closeJumpModal();
                return;
            }

            const stepperBtn = e.target.closest(STEPPER_SELECTOR);
            if (stepperBtn) {
                const delta = parseInt(stepperBtn.dataset.step, 10);
                const current = parseInt(jumpInput.value, 10) || 0;
                const next = current + delta;

                if (next >= 1 && next <= totalPages) {
                    jumpInput.value = next;
                }
            }
        });

        jumpModal.addEventListener('click', (e) => {
            if (e.target === jumpModal) {
                closeJumpModal();
            }
        });

        jumpInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                executeJump();
            }
        });
    });
})();
