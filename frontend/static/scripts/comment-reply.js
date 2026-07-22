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
                        if (otherToggle) otherToggle.textContent = otherToggle.dataset.replyText;
                    }
                });

                document.querySelectorAll('.edit-form-container').forEach(other => {
                    if (other.style.display === 'block') {
                        other.style.display = 'none';
                        const otherId = other.id.replace('edit-form-', '');
                        const otherToggle = document.querySelector('.comment-edit-toggle[data-comment-id="' + otherId + '"]');
                        if (otherToggle) otherToggle.textContent = otherToggle.dataset.editText;
                        const otherBody = document.getElementById('comment-body-' + otherId);
                        if (otherBody) otherBody.style.display = '';
                    }
                });

                const isHidden = container.style.display === 'none';
                container.style.display = isHidden ? 'block' : 'none';
                replyToggle.textContent = isHidden ? replyToggle.dataset.cancelText : replyToggle.dataset.replyText;

                if (isHidden && window.initReplyEditor) {
                    window.initReplyEditor(commentId);
                }
                return;
            }

            const viewBtn = e.target.closest('.view-replies-btn');
            if (viewBtn) {
                const commentEl = viewBtn.closest('.comment');
                if (!commentEl) return;
                commentEl.classList.toggle('replies-visible');
                const isVisible = commentEl.classList.contains('replies-visible');
                viewBtn.textContent = isVisible ? viewBtn.dataset.hideText : viewBtn.dataset.showText;

                const cascade = (el, visible) => {
                    const replies = el.querySelector(':scope > .comment-content > .comment-replies');
                    if (!replies) return;
                    replies.querySelectorAll(':scope > .comment').forEach(child => {
                        child.classList.toggle('replies-visible', visible);
                        const btn = child.querySelector('.view-replies-btn');
                        if (btn) btn.textContent = visible ? btn.dataset.hideText : btn.dataset.showText;
                        cascade(child, visible);
                    });
                };
                cascade(commentEl, isVisible);
                return;
            }

            const editToggle = e.target.closest('.comment-edit-toggle');
            if (editToggle) {
                e.preventDefault();
                const commentId = editToggle.dataset.commentId;
                const container = document.getElementById('edit-form-' + commentId);
                if (!container) return;

                document.querySelectorAll('.edit-form-container').forEach(other => {
                    if (other.style.display === 'block' && other.id !== container.id) {
                        other.style.display = 'none';
                        const otherId = other.id.replace('edit-form-', '');
                        const otherToggle = document.querySelector('.comment-edit-toggle[data-comment-id="' + otherId + '"]');
                        if (otherToggle) otherToggle.textContent = otherToggle.dataset.editText;
                        const otherBody = document.getElementById('comment-body-' + otherId);
                        if (otherBody) {
                            otherBody.style.display = '';
                            const otherEdited = otherBody.nextElementSibling;
                            if (otherEdited && otherEdited.classList.contains('comment-edited-line')) {
                                otherEdited.style.display = '';
                            }
                        }
                    }
                });

                document.querySelectorAll('.reply-form-container').forEach(other => {
                    if (other.style.display === 'block') {
                        other.style.display = 'none';
                        const otherId = other.id.replace('reply-form-', '');
                        const otherToggle = document.querySelector('.reply-toggle[data-comment-id="' + otherId + '"]');
                        if (otherToggle) otherToggle.textContent = otherToggle.dataset.replyText;
                    }
                });

                const isHidden = container.style.display === 'none';
                container.style.display = isHidden ? 'block' : 'none';
                editToggle.textContent = isHidden ? editToggle.dataset.cancelText : editToggle.dataset.editText;

                const bodyText = document.getElementById('comment-body-' + commentId);
                if (bodyText) {
                    bodyText.style.display = isHidden ? 'none' : '';
                    const editedLine = bodyText.nextElementSibling;
                    if (editedLine && editedLine.classList.contains('comment-edited-line')) {
                        editedLine.style.display = isHidden ? 'none' : '';
                    }
                }

                if (isHidden && window.initEditEditor) {
                    window.initEditEditor(commentId);
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
                    toggle.textContent = toggle.dataset.replyText;
                }
                return;
            }

            const cancelEdit = e.target.closest('.cancel-edit');
            if (cancelEdit) {
                const container = cancelEdit.closest('.edit-form-container');
                if (!container) return;
                container.style.display = 'none';
                const commentId = container.id.replace('edit-form-', '');
                const toggle = document.querySelector('.comment-edit-toggle[data-comment-id="' + commentId + '"]');
                if (toggle) {
                    toggle.textContent = toggle.dataset.editText;
                }
                const bodyText = document.getElementById('comment-body-' + commentId);
                if (bodyText) {
                    bodyText.style.display = '';
                    const editedLine = bodyText.nextElementSibling;
                    if (editedLine && editedLine.classList.contains('comment-edited-line')) {
                        editedLine.style.display = '';
                    }
                }
                return;
            }
        });
    });
})();
