'use strict';

(() => {
    document.addEventListener('DOMContentLoaded', () => {
        document.addEventListener('click', (e) => {
            const replyToggle = e.target.closest('.reply-toggle');
            if (replyToggle) {
                e.preventDefault();
                const commentId = replyToggle.dataset.commentId;
                const container = document.getElementById('reply-form-' + commentId);
                if (!container) return;

                document.querySelectorAll('.reply-form-container').forEach(other => {
                    if (other.style.display === 'block' && other.id !== container.id) {
                        other.style.display = 'none';
                        const otherId = other.id.replace('reply-form-', '');
                        const otherToggle = document.querySelector('.reply-toggle[data-comment-id="' + otherId + '"]');
                        if (otherToggle) otherToggle.textContent = 'Reply';
                    }
                });

                const isHidden = container.style.display === 'none';
                container.style.display = isHidden ? 'block' : 'none';
                replyToggle.textContent = isHidden ? 'Cancel' : 'Reply';

                if (isHidden && window.__initReplyEditor) {
                    window.__initReplyEditor(commentId);
                }
                return;
            }

            const cancelBtn = e.target.closest('.cancel-reply');
            if (cancelBtn) {
                const container = cancelBtn.closest('.reply-form-container');
                if (!container) return;
                container.style.display = 'none';
                const commentId = container.id.replace('reply-form-', '');
                const toggle = document.querySelector('.reply-toggle[data-comment-id="' + commentId + '"]');
                if (toggle) {
                    toggle.textContent = 'Reply';
                }
            }
        });
    });
})();
