'use strict';

(() => {
    const _t = key => {
        const el = document.getElementById('app-translations');
        if (!el) return key;
        try { return JSON.parse(el.textContent)[key] || key; } catch { return key; }
    };

    const activeMode = { type: null, commentId: null, button: null };

    function restoreButtonText() {
        if (!activeMode.button) return;
        if (activeMode.type === 'reply') activeMode.button.textContent = _t('Reply');
        else if (activeMode.type === 'edit') activeMode.button.textContent = _t('[Edit]');
    }

    function resetForm() {
        const form = document.getElementById('comment-form');
        form.action = form.dataset.createUrl;

        document.getElementById('comment-submit-btn').textContent = _t('Post Comment');
        document.getElementById('cancel-edit-btn').style.display = 'none';
        document.getElementById('comment-form-title').textContent = _t('Join the discussion');

        restoreButtonText();
        activeMode.type = null;
        activeMode.commentId = null;
        activeMode.button = null;

        if (window.clearCommentEditor) {
            window.clearCommentEditor();
        }
    }

    function enterReplyMode(replyToggle) {
        const commentId = replyToggle.dataset.commentId;
        const form = document.getElementById('comment-form');
        const replyUrl = form.dataset.replyUrl.replace(/\/comments\/0\/reply$/, '/comments/' + commentId + '/reply');
        form.action = replyUrl;

        document.getElementById('comment-submit-btn').textContent = _t('Reply');
        document.getElementById('cancel-edit-btn').style.display = '';
        document.getElementById('comment-form-title').textContent = _t('Reply to') + ' ' + (replyToggle.dataset.authorUsername || _t('Anonymous'));

        restoreButtonText();
        replyToggle.textContent = _t('Cancel');
        activeMode.type = 'reply';
        activeMode.commentId = commentId;
        activeMode.button = replyToggle;

        if (window.clearCommentEditor) {
            window.clearCommentEditor();
        }

        document.getElementById('comment-form-title').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function enterEditMode(editToggle) {
        const commentId = editToggle.dataset.commentId;
        const bodyEl = document.getElementById('comment-body-' + commentId);
        if (!bodyEl) return;

        const contentHtml = bodyEl.innerHTML;

        const form = document.getElementById('comment-form');
        const editUrl = form.dataset.editUrl.replace(/\/comments\/0\/edit$/, '/comments/' + commentId + '/edit');
        form.action = editUrl;

        document.getElementById('comment-submit-btn').textContent = _t('Save');
        document.getElementById('cancel-edit-btn').style.display = '';
        document.getElementById('comment-form-title').textContent = _t('Editing comment');

        restoreButtonText();
        editToggle.textContent = _t('Cancel');
        activeMode.type = 'edit';
        activeMode.commentId = commentId;
        activeMode.button = editToggle;

        if (window.setCommentEditorContent) {
            window.setCommentEditorContent(contentHtml);
        }

        document.getElementById('comment-form-title').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.addEventListener('click', (e) => {
            const replyToggle = e.target.closest('.reply-toggle');
            if (replyToggle) {
                e.preventDefault();
                const commentId = replyToggle.dataset.commentId;
                if (activeMode.type === 'reply' && activeMode.commentId === commentId) {
                    resetForm();
                } else {
                    enterReplyMode(replyToggle);
                }
                return;
            }

            const editToggle = e.target.closest('.comment-edit-toggle');
            if (editToggle) {
                e.preventDefault();
                const commentId = editToggle.dataset.commentId;
                if (activeMode.type === 'edit' && activeMode.commentId === commentId) {
                    resetForm();
                } else {
                    enterEditMode(editToggle);
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

            const cancelEditBtn = e.target.closest('#cancel-edit-btn');
            if (cancelEditBtn) {
                resetForm();
                return;
            }
        });
    });
})();
