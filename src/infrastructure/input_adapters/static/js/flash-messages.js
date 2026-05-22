"use strict";

(() => {
    try {
        const initFlashDismiss = function () {
            const alerts = document.querySelectorAll('.flash-messages .alert');
            alerts.forEach(function (alert) {
                alert.addEventListener('animationend', function (e) {
                    if (e.animationName === 'flash-fade-out') {
                        const container = alert.parentElement;
                        alert.remove();
                        if (container && container.children.length === 0) {
                            container.remove();
                        }
                    }
                });
            });
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initFlashDismiss);
        } else {
            initFlashDismiss();
        }
    } catch (error) {
        console.warn('DevJournal: Failed to initialize flash auto-dismiss.', error);
    }
})();
