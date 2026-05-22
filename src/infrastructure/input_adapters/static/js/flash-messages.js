"use strict";

(() => {
    try {
        const removeAlert = (alert) => {
            const container = alert.parentElement;
            alert.remove();
            if (container && container.children.length === 0) {
                container.remove();
            }
        };

        const initFlashDismiss = () => {
            const alerts = document.querySelectorAll('.flash-messages .alert');
            alerts.forEach((alert) => {
                let removed = false;
                const safeRemove = () => {
                    if (removed) return;
                    removed = true;
                    removeAlert(alert);
                };

                alert.addEventListener('animationend', (e) => {
                    if (e.animationName === 'flash-fade-out') safeRemove();
                });
                setTimeout(safeRemove, 3500);
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
