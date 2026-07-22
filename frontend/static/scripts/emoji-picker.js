'use strict';

(() => {
    let activePopup = null;

    function closePopup() {
        if (activePopup) {
            activePopup.remove();
            activePopup = null;
        }
    }

    function openPicker(anchorRect, editorId) {
        closePopup();

        const theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';

        const popup = document.createElement('DIV');
        popup.className = 'emoji-picker-popup';
        popup.style.position = 'fixed';
        popup.style.left = anchorRect.left + 'px';
        popup.style.top = (anchorRect.top + 4) + 'px';
        popup.style.zIndex = '9999';

        const picker = new EmojiMart.Picker({
            theme: theme,
            set: 'native',
            maxFrequentRows: 4,
            previewPosition: 'none',
            skinTonePosition: 'none',
            i18n: {
                search: 'Rechercher',
                'search_no_results_1': 'Oh non\u00a0!',
                'search_no_results_2': 'Cet emoji est introuvable',
                pick: 'Choisissez un emoji\u2026',
                categories: {
                    activity: 'Activit\u00e9s',
                    custom: 'Personnalis\u00e9s',
                    flags: 'Drapeaux',
                    foods: 'Aliments & Boissons',
                    frequent: 'Utilis\u00e9s fr\u00e9quemment',
                    nature: 'Animaux & Nature',
                    objects: 'Objets',
                    people: 'Smileys & Personnes',
                    places: 'Voyages & Lieux',
                    search: 'R\u00e9sultats de recherche',
                    symbols: 'Symboles',
                },
                skins: {
                    '1': 'Par d\u00e9faut',
                    '2': 'Clair',
                    '3': 'Moyen-Clair',
                    '4': 'Moyen',
                    '5': 'Moyen-Fonc\u00e9',
                    '6': 'Fonc\u00e9',
                    choose: 'Choisir le teint de peau par d\u00e9faut',
                },
            },
            onEmojiSelect: function (data) {
                const editor = window.suneditors[editorId];
                if (editor) {
                    editor.insertHTML(data.native);
                }
                closePopup();
            }
        });

        popup.appendChild(picker);
        document.body.appendChild(popup);
        activePopup = popup;

        requestAnimationFrame(function () {
            const pr = popup.getBoundingClientRect();
            const overflowRight = pr.right - window.innerWidth;
            const overflowBottom = pr.bottom - window.innerHeight;

            if (overflowRight > 0) {
                popup.style.left = Math.max(4, pr.left - overflowRight - 4) + 'px';
            }
            if (overflowBottom > 0) {
                popup.style.top = Math.max(4, anchorRect.top - pr.height - 4) + 'px';
            }
        });
    }

    document.addEventListener('click', function (e) {
        if (activePopup && !activePopup.contains(e.target) && !e.target.closest('[data-command]')) {
            closePopup();
        }
    });

    window.addEventListener('scroll', function (e) {
        if (activePopup && !activePopup.contains(e.target)) {
            closePopup();
        }
    }, true);

    window.addEventListener('open-emoji-picker', function (e) {
        if (activePopup) {
            closePopup();
            return;
        }
        openPicker({
            left: e.detail.left,
            top: e.detail.top
        }, e.detail.editorId);
    });
})();
