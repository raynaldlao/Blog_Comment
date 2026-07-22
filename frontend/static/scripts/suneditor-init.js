'use strict';

const _t = key => {
    const el = document.getElementById('app-translations');
    if (!el) return key;
    try { return JSON.parse(el.textContent)[key] || key; } catch { return key; }
};

function resolveLang(flat) {
    if (!flat) return null;
    const dst = { toolbar: {}, controller: {}, menu: {}, dialogBox: {} };
    const boxMap = { linkBox: {}, imageBox: {}, videoBox: {}, audioBox: {}, mathBox: {} };
    for (const boxKey of Object.keys(boxMap)) dst.dialogBox[boxKey] = {};

    const mappings = [
        ['bold', 'toolbar'], ['italic', 'toolbar'], ['underline', 'toolbar'],
        ['strike', 'toolbar'], ['list', 'toolbar'], ['link', 'toolbar'],
        ['align', 'toolbar'], ['font', 'toolbar'], ['fontSize', 'toolbar'],
        ['fontColor', 'toolbar'], ['backgroundColor', 'toolbar'],
        ['indent', 'toolbar'], ['outdent', 'toolbar'],
        ['alignLeft', 'toolbar'], ['alignCenter', 'toolbar'],
        ['alignRight', 'toolbar'], ['alignJustify', 'toolbar'],
        ['codeView', 'toolbar'], ['fullScreen', 'toolbar'],
        ['undo', 'toolbar'], ['redo', 'toolbar'], ['save', 'toolbar'],
        ['print', 'toolbar'], ['preview', 'toolbar'],
        ['removeFormat', 'toolbar'], ['copyFormat', 'toolbar'],
        ['table', 'toolbar'], ['image', 'toolbar'], ['video', 'toolbar'],
        ['audio', 'toolbar'], ['math', 'toolbar'],
        ['horizontalRule', 'toolbar'],
        ['imageGallery', 'toolbar'], ['fileBrowser', 'toolbar'],
        ['fileGallery', 'toolbar'], ['mediaGallery', 'toolbar'],
        ['videoGallery', 'toolbar'], ['audioGallery', 'toolbar'],

        ['maxSize', 'controller'], ['minSize', 'controller'],
        ['resize', 'controller'], ['resize100', 'controller'],
        ['resize25', 'controller'], ['resize50', 'controller'],
        ['resize75', 'controller'], ['proportion', 'controller'],
        ['ratio', 'controller'], ['rotateLeft', 'controller'],
        ['rotateRight', 'controller'],
        ['mirrorHorizontal', 'controller'], ['mirrorVertical', 'controller'],
        ['edit', 'controller'], ['remove', 'controller'],
        ['unlink', 'controller'], ['autoSize', 'controller'],
        ['deleteColumn', 'controller'], ['deleteRow', 'controller'],
        ['fixedColumnWidth', 'controller'],
        ['insertColumnAfter', 'controller'], ['insertColumnBefore', 'controller'],
        ['insertRowAbove', 'controller'], ['insertRowBelow', 'controller'],
        ['mergeCells', 'controller'], ['splitCells', 'controller'],
        ['tableHeader', 'controller'],

        ['close', 'dialogBox'], ['caption', 'dialogBox'],
        ['submitButton', 'dialogBox'], ['basic', 'dialogBox'],
        ['cancel', 'dialogBox'],
    ];

    for (const [key, ...path] of mappings) {
        if (flat[key] === undefined) continue;
        let obj = dst;
            for (let i = 0; i < path.length; i++) obj = obj[path[i]];
            obj[key] = flat[key];
    }

    const menuKeys = ['menu_bordered', 'menu_code', 'menu_neon', 'menu_shadow', 'menu_spaced', 'menu_translucent'];
    for (const key of menuKeys) {
        if (flat[key] === undefined) continue;
        dst.menu[key.slice(5)] = flat[key];
    }

    const modalPrefixes = [
        { prefix: 'link_modal_', box: 'linkBox' },
        { prefix: 'image_modal_', box: 'imageBox' },
        { prefix: 'video_modal_', box: 'videoBox' },
        { prefix: 'audio_modal_', box: 'audioBox' },
        { prefix: 'math_modal_', box: 'mathBox' },
    ];
    for (const { prefix, box } of modalPrefixes) {
        for (const key of Object.keys(flat)) {
            if (!key.startsWith(prefix)) continue;
            dst.dialogBox[box][key.slice(prefix.length)] = flat[key];
        }
    }

    return dst;
}

(() => {
    function createEmojiPlugin(textareaId) {
        return {
            name: 'emoji',
            display: 'command',
            active: function () { return true; },
            title: _t('Insert Emoji'),
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
            lang: resolveLang(SUNEDITOR_LANG && SUNEDITOR_LANG.fr),
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

            let lastTap = null;
            wysiwyg.addEventListener('click', () => {
                const now = Date.now();
                if (lastTap && now - lastTap < 400) {
                    const range = document.createRange();
                    range.selectNodeContents(wysiwyg);
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                    lastTap = null;
                } else {
                    lastTap = now;
                }
            });
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
                    showToast(_t('Comment cannot be empty'));
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

    window.initEditEditor = function (commentId) {
        initCommentEditor('edit-editor-' + commentId, 'edit-content-' + commentId);
    };

    document.addEventListener('DOMContentLoaded', () => {
        initCommentEditor('comment-editor', 'comment-content');
    });
})();
