"use strict";

(() => {
    const STORAGE_KEY = 'blog_theme';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';

    const getStoredTheme = () => {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            console.warn("DevJournal : Unable to read theme from localStorage.", e);
            return null;
        }
    };

    const setStoredTheme = (theme) => {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {
            console.warn("DevJournal : Unable to save theme to localStorage.", e);
        }
    };


    document.addEventListener('DOMContentLoaded', () => {
        const applyTheme = (theme) => {
            document.documentElement.dataset.theme = theme;
        };

        const toggleBtn = document.getElementById('theme-toggle-btn');
        const iconElement = toggleBtn ? toggleBtn.querySelector('.material-symbols-outlined') : null;

        if (!toggleBtn || !iconElement) return;

        const updateIcon = (theme) => {
            iconElement.textContent = theme === THEME_LIGHT ? 'dark_mode' : 'light_mode';
        };

        updateIcon(document.documentElement.dataset.theme);

        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.dataset.theme;
            const target = current === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;

            applyTheme(target);
            setStoredTheme(target);
            updateIcon(target);
        });

        const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        const handleSystemChange = (e) => {
            if (!getStoredTheme()) {
                const newTheme = e.matches ? THEME_LIGHT : THEME_DARK;
                applyTheme(newTheme);
                updateIcon(newTheme);
            }
        };

        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', handleSystemChange);
        } else if (mediaQuery.addListener) {
            mediaQuery.addListener(handleSystemChange);
        }
    });
})();
