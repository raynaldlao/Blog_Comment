(function () {
    'use strict';

    window.__suneditors = {};

    function createEmojiPlugin(textareaId) {
        return {
            name: 'emoji',
            display: 'command',
            active: function () { return true; },
            title: 'Insert Emoji',
            innerHTML: '\uD83D\uDE0A',
            add: function (core, buttonElement) {
                buttonElement.dataset.editorId = textareaId;
            },
            action: function () {
                var btn = this.commandMap && this.commandMap.emoji;
                if (btn) {
                    var rect = btn.getBoundingClientRect();
                    window.dispatchEvent(new CustomEvent('open-emoji-picker', {
                        detail: {
                            editorId: btn.dataset.editorId,
                            left: rect.left,
                            top: rect.bottom + 4
                        }
                    }));
                }
            }
        };
    }

    function initCommentEditor(textareaId, hiddenInputId) {
        var textarea = document.getElementById(textareaId);
        if (!textarea || textarea.dataset.suneditor) return;

        var form = textarea.closest('form');
        var hiddenInput = hiddenInputId ? document.getElementById(hiddenInputId) : null;

        var editor = SUNEDITOR.create(textarea, {
            plugins: [createEmojiPlugin(textareaId)],
            buttonList: [
                ['bold', 'underline', 'italic', 'strike'],
                ['list', 'link', 'emoji']
            ],
            height: 'auto',
            minHeight: '6.25rem',
        });

        window.__suneditors[textareaId] = editor;

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
