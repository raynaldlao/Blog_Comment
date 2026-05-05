"use strict";

(() => {
    document.addEventListener('DOMContentLoaded', () => {
        const jumpModal = document.getElementById('jump-modal');
        if (!jumpModal) return;

        const jumpInput = document.getElementById('jump-page-input');
        const totalPages = parseInt(jumpModal.dataset.totalPages, 10);
        const baseUrl = jumpModal.dataset.url;

        const openJumpModal = () => {
            jumpModal.showModal();
            jumpInput.value = '';
            setTimeout(() => jumpInput.focus(), 50);
        };

        jumpInput.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9]/g, '');
        });

        const closeJumpModal = () => jumpModal.close();

        const executeJump = () => {
            const val = parseInt(jumpInput.value, 10);
            if (val && val >= 1 && val <= totalPages) {
                window.location.href = `${baseUrl}?page=${val}`;
            } else {
                jumpInput.classList.add('input-error');
                setTimeout(() => {
                    jumpInput.classList.remove('input-error');
                }, 500);
            }
        };

        document.addEventListener('click', (e) => {
            if (e.target.closest('.jump-modal-trigger')) {
                openJumpModal();
                return;
            }

            const id = e.target.id;
            if (id === 'jump-execute-btn') {
                executeJump();
                return;
            }
            if (id === 'jump-cancel-btn') {
                closeJumpModal();
                return;
            }

            const stepperBtn = e.target.closest('.stepper-btn');
            if (stepperBtn) {
                const delta = parseInt(stepperBtn.dataset.step, 10);
                const current = parseInt(jumpInput.value, 10) || 1;
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

        jumpInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                executeJump();
            }
        });
    });
})();
