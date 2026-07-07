(function () {
    'use strict';

    function initCommentEditor(textareaId, hiddenInputId) {
        var textarea = document.getElementById(textareaId);
        if (!textarea || textarea.dataset.suneditor) return;

        var editor = SUNEDITOR.create(textarea, {
            buttonList: [
                ['bold', 'underline', 'italic', 'strike'],
                ['list', 'link'],
                ['emoji']
            ],
            height: 'auto',
            minHeight: '6.25rem',
        });

        var form = textarea.closest('form');
        if (form && hiddenInputId) {
            var hiddenInput = document.getElementById(hiddenInputId);
            if (hiddenInput) {
                form.addEventListener('submit', function () {
                    hiddenInput.value = editor.getContents();
                });
            }
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
