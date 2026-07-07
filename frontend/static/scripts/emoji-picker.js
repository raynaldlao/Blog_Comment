(function () {
    'use strict';

    var activePopup = null;

    function closePopup() {
        if (activePopup) {
            activePopup.remove();
            activePopup = null;
        }
    }

    function openPicker(anchorRect, editorId) {
        closePopup();

        var theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';

        var popup = document.createElement('DIV');
        popup.className = 'emoji-picker-popup';
        popup.style.position = 'fixed';
        popup.style.left = anchorRect.left + 'px';
        popup.style.top = anchorRect.top + 'px';
        popup.style.zIndex = '9999';

        var picker = new EmojiMart.Picker({
            theme: theme,
            set: 'native',
            maxFrequentRows: 4,
            previewPosition: 'none',
            onEmojiSelect: function (data) {
                var editor = window.__suneditors[editorId];
                if (editor) {
                    editor.insertHTML(data.native);
                }
                closePopup();
            }
        });

        popup.appendChild(picker);
        document.body.appendChild(popup);
        activePopup = popup;
    }

    document.addEventListener('click', function (e) {
        if (activePopup && !activePopup.contains(e.target) && !e.target.closest('[data-command]')) {
            closePopup();
        }
    });

    window.addEventListener('open-emoji-picker', function (e) {
        openPicker({
            left: e.detail.left,
            top: e.detail.top
        }, e.detail.editorId);
    });
})();
