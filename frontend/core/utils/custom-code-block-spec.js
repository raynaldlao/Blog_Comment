import { createCodeBlockSpec as createOriginalCodeBlockSpec } from '@blocknote/core';

const DEBUG = false;
const dbg = (...args) => { if (DEBUG) console.log('[LANG-SEL]', ...args); };

function createLanguageSelectorWidget(select, block, editor) {
  try {
    dbg('widget creation for block', block.id);
    const container = document.createElement('div');
    container.className = 'code-block-lang-selector';

    const trigger = document.createElement('button');
    trigger.className = 'code-block-lang-trigger';
    trigger.textContent = select.options[select.selectedIndex]?.text || 'Plain Text';
    trigger.tabIndex = 0;

    const dropdown = document.createElement('div');
    dropdown.className = 'code-block-lang-dropdown';

    const searchWrap = document.createElement('div');
    searchWrap.className = 'code-block-lang-search-wrap';

    const searchIcon = document.createElement('span');
    searchIcon.className = 'code-block-lang-search-icon';
    searchIcon.textContent = '\u{1F50D}';

    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Search languages...';
    searchInput.className = 'code-block-lang-search';

    searchWrap.appendChild(searchIcon);
    searchWrap.appendChild(searchInput);

    const separator = document.createElement('div');
    separator.className = 'code-block-lang-separator';

    const list = document.createElement('div');
    list.className = 'code-block-lang-list';

    const items = [];
    const noResultsMsg = document.createElement('div');
    noResultsMsg.className = 'code-block-lang-no-results';
    noResultsMsg.textContent = 'No languages found';
    noResultsMsg.style.display = 'none';

    Array.from(select.options).forEach((opt) => {
      const item = document.createElement('div');
      item.className = 'code-block-lang-item';
      if (opt.value === select.value) {
        item.classList.add('code-block-lang-item--selected');
      }
      item.dataset.lang = opt.value;
      item.textContent = opt.text;
      item.addEventListener('click', () => {
        select.value = opt.value;
        select.dispatchEvent(new Event('change'));
        trigger.textContent = opt.text;
        closeDropdown();
      });
      list.appendChild(item);
      items.push(item);
    });

    function updateNoResults() {
      const hasVisible = items.some((item) => item.style.display !== 'none');
      noResultsMsg.style.display = hasVisible ? 'none' : '';
    }

    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase();
      items.forEach((item) => {
        const match = item.textContent.toLowerCase().includes(q);
        item.style.display = match ? '' : 'none';
      });
      updateNoResults();
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        closeDropdown();
        trigger.focus();
        return;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        focusNextItem(1);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        focusNextItem(-1);
        return;
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        const focused = list.querySelector('.code-block-lang-item--focused');
        if (focused) {
          focused.click();
        } else {
          const first = items.find((item) => item.style.display !== 'none');
          if (first) first.click();
        }
      }
    });

    function focusNextItem(dir) {
      const visible = items.filter((item) => item.style.display !== 'none');
      if (visible.length === 0) return;
      const currentIndex = visible.findIndex((item) =>
        item.classList.contains('code-block-lang-item--focused')
      );
      const nextIndex = currentIndex === -1
        ? (dir > 0 ? 0 : visible.length - 1)
        : Math.max(0, Math.min(visible.length - 1, currentIndex + dir));
      visible.forEach((item) => item.classList.remove('code-block-lang-item--focused'));
      visible[nextIndex].classList.add('code-block-lang-item--focused');
      visible[nextIndex].scrollIntoView({ block: 'nearest' });
    }

    function positionLangDropdown() {
      const rect = trigger.getBoundingClientRect();
      const gap = 4;
      dropdown.style.top = (rect.bottom + gap) + 'px';
      dropdown.style.left = Math.max(8, rect.left) + 'px';
    }

    function onDocumentClick(e) {
      const isInside = dropdown.contains(e.target) || trigger.contains(e.target);
      dbg('doc click', { inside: isInside, target: e.target.className || e.target.tagName, time: Date.now() });
      if (!isInside) {
        dbg('closing due to outside click');
        closeDropdown();
      }
    }

    function onScroll() {
      if (dropdown.classList.contains('code-block-lang-dropdown--open')) {
        positionLangDropdown();
      }
    }

    function openDropdown() {
      dbg('openDropdown', { time: Date.now() });
      searchInput.value = '';
      items.forEach((item) => {
        item.style.display = '';
        item.classList.remove('code-block-lang-item--focused');
      });
      noResultsMsg.style.display = 'none';
      positionLangDropdown();
      document.body.appendChild(dropdown);
      dropdown.classList.add('code-block-lang-dropdown--open');
      searchInput.focus();
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('scroll', onScroll, { passive: true });
    }

    function closeDropdown() {
      dbg('closeDropdown', { time: Date.now() });
      dropdown.classList.remove('code-block-lang-dropdown--open');
      if (dropdown.parentElement) {
        dropdown.parentElement.removeChild(dropdown);
      }
      document.removeEventListener('click', onDocumentClick);
      document.removeEventListener('scroll', onScroll, { passive: true });
    }

    trigger.addEventListener('mousedown', (e) => {
      e.stopPropagation();
    });

    trigger.addEventListener('click', (e) => {
      if (dropdown.classList.contains('code-block-lang-dropdown--open')) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    dropdown.addEventListener('mousedown', (e) => {
      e.stopPropagation();
    });

    select.addEventListener('change', () => {
      trigger.textContent = select.options[select.selectedIndex]?.text || 'Plain Text';
    });

    dropdown.appendChild(searchWrap);
    dropdown.appendChild(separator);
    dropdown.appendChild(noResultsMsg);
    dropdown.appendChild(list);
    container.appendChild(trigger);

    container._closeDropdown = closeDropdown;

    select.style.display = 'none';
    const parent = select.parentElement;
    if (parent) {
      parent.appendChild(container);
    }

    return container;
  } catch (e) {
    console.error('Language selector widget failed:', e);
    select.style.display = '';
    return null;
  }
}

export function createCustomCodeBlockSpec(options) {
  const spec = createOriginalCodeBlockSpec(options);
  const originalRender = spec.implementation.render.bind(spec.implementation);

  let widgetInstance = null;

  function ensureCopyButton(dom, lang) {
    if (dom.classList.contains('code-block-wrapper')) return;
    dom.classList.add('code-block-wrapper');
    const btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = 'Copy';
    if (lang) btn.dataset.lang = lang;
    dom.appendChild(btn);
  }

  spec.implementation.render = (block, editor) => {
    const result = originalRender(block, editor);
    dbg('render() called for block', block.id, { hasExisting: widgetInstance !== null, time: Date.now() });

    const selectEl = result.dom.querySelector('select');
    const codeEl = result.dom.querySelector('code');
    const lang = selectEl?.value
        || Array.from(codeEl?.classList || []).find((c) => c.startsWith('language-'))?.replace('language-', '')
        || '';
    ensureCopyButton(result.dom, lang);

    if (!editor.isEditable) {
      return result;
    }

    const wrapperDiv = result.dom.querySelector('[contenteditable="false"]');
    if (wrapperDiv) {
      const select = wrapperDiv.querySelector('select');
      if (select && select.options.length > 0) {
        if (widgetInstance) {
          dbg('cleanup old widget before recreating', block.id);
          widgetInstance._closeDropdown?.();
        }
        widgetInstance = createLanguageSelectorWidget(select, block, editor);
      }
    }

    return result;
  };

  return spec;
}
