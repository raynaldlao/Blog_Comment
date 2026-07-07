(function () {
    'use strict';

    function initCommentEditor(textareaId, hiddenInputId) {
        var textarea = document.getElementById(textareaId);
        if (!textarea || textarea.dataset.suneditor) return;

        var form = textarea.closest('form');
        var hiddenInput = hiddenInputId ? document.getElementById(hiddenInputId) : null;

        var editor = SUNEDITOR.create(textarea, {
            buttonList: [
                ['bold', 'underline', 'italic', 'strike'],
                ['list', 'link']
            ],
            height: 'auto',
            minHeight: '6.25rem',
        });

        if (form && hiddenInput) {
            form.addEventListener('submit', function () {
                hiddenInput.value = editor.getContents();
            });
        }

        textarea.dataset.suneditor = 'true';
    }

    window.__initReplyEditor = function (commentId) {
        initCommentEditor('reply-editor-' + commentId, 'reply-content-' + commentId);
    };

    document.addEventListener('DOMContentLoaded', function () {
        initCommentEditor('comment-editor', 'comment-content');
    });
})();
