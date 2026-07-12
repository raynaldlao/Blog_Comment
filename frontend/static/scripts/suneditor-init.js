'use strict';

(() => {
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
                const btn = this.commandMap && this.commandMap.emoji;
                if (btn) {
                    const rect = btn.getBoundingClientRect();
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

    function showToast(message) {
        const oldToast = document.querySelector('.toast');
        if (oldToast) oldToast.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 2800);
    }

    const suneditors = {};

    function initCommentEditor(textareaId, hiddenInputId) {
        const textarea = document.getElementById(textareaId);
        if (!textarea || textarea.dataset.suneditor) return;

        const form = textarea.closest('form');
        const hiddenInput = hiddenInputId ? document.getElementById(hiddenInputId) : null;

        const editor = SUNEDITOR.create(textarea, {
            plugins: [createEmojiPlugin(textareaId)],
            buttonList: [
                ['bold', 'underline', 'italic', 'strike'],
                ['list', 'link', 'emoji']
            ],
            lineHeight: '1.4',
            imageUploadUrl: '',
            imageFileInput: false,
            imageUrlInput: false,
            onPaste: function (e, cleanData, maxCharCount) {
                if (e.clipboardData && e.clipboardData.files) {
                    for (let i = 0; i < e.clipboardData.files.length; i++) {
                        if (e.clipboardData.files[i].type.startsWith('image/')) {
                            e.preventDefault();
                            return '';
                        }
                    }
                }
                return cleanData.replace(/<img[^>]*>/gi, '');
            },
            height: 'auto',
            minHeight: '6.25rem',
            maxCharCount: 5000,
        });

        suneditors[textareaId] = editor;

        const wysiwyg = textarea.nextElementSibling?.querySelector('.sun-editor-editable');
        if (wysiwyg) {
            wysiwyg.addEventListener('paste', (e) => {
                const items = e.clipboardData?.items;
                if (items) {
                    for (const item of items) {
                        if (item.type.startsWith('image/')) {
                            e.preventDefault();
                            e.stopPropagation();
                            return;
                        }
                    }
                }
                const html = e.clipboardData?.getData('text/html');
                if (html && /<img[^>]*>/i.test(html)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }, true);

            wysiwyg.addEventListener('drop', (e) => {
                const files = e.dataTransfer?.files;
                if (files) {
                    for (const file of files) {
                        if (file.type.startsWith('image/')) {
                            e.preventDefault();
                            e.stopPropagation();
                            return;
                        }
                    }
                }
            }, true);
        }

        editor.insertImage = function () {
            return null;
        };

        if (form && hiddenInput) {
            form.addEventListener('submit', function (e) {
                const html = editor.getContents();
                const text = html.replace(/<[^>]+>/g, '').trim();
                if (!text) {
                    e.preventDefault();
                    showToast('Comment cannot be empty');
                    return;
                }
                hiddenInput.value = html;
            });
        }

        textarea.dataset.suneditor = 'true';
    }

    window.initReplyEditor = function (commentId) {
        initCommentEditor('reply-editor-' + commentId, 'reply-content-' + commentId);
    };

    document.addEventListener('DOMContentLoaded', () => {
        initCommentEditor('comment-editor', 'comment-content');
    });
})();
