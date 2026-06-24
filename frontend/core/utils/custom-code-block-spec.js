import { createCodeBlockSpec as createOriginalCodeBlockSpec } from '@blocknote/core';

function createLanguageSelectorWidget(select, block, editor) {
  try {
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
    searchIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" height="24" viewBox="0 -960 960 960" width="24"><path d="M784-120 532-372q-30 24-69 38t-83 14q-109 0-184.5-75.5T120-580q0-109 75.5-184.5T380-840q109 0 184.5 75.5T640-580q0 44-14 83t-38 69l252 252-56 56ZM380-400q75 0 127.5-52.5T560-580q0-75-52.5-127.5T380-760q-75 0-127.5 52.5T200-580q0 75 52.5 127.5T380-400Z"/></svg>';

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
      if (!isInside) {
        closeDropdown();
      }
    }

    function onScroll() {
      if (dropdown.classList.contains('code-block-lang-dropdown--open')) {
        positionLangDropdown();
      }
    }

    function openDropdown() {
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

  function ensureHeaderButtons(dom, lang, block, editor) {
    if (dom.classList.contains('code-block-wrapper')) return;
    dom.classList.add('code-block-wrapper');

    const actions = document.createElement('div');
    actions.className = 'code-block-actions';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'code-copy-btn';
    copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="1em" height="1em"><path d="M6.9998 6V3C6.9998 2.44772 7.44752 2 7.9998 2H19.9998C20.5521 2 20.9998 2.44772 20.9998 3V17C20.9998 17.5523 20.5521 18 19.9998 18H16.9998V20.9991C16.9998 21.5519 16.5499 22 15.993 22H4.00666C3.45059 22 3 21.5554 3 20.9991L3.0026 7.00087C3.0027 6.44811 3.45264 6 4.00942 6H6.9998ZM5.00242 8L5.00019 20H14.9998V8H5.00242ZM8.9998 6H16.9998V16H18.9998V4H8.9998V6Z"/></svg>';
    if (lang) copyBtn.dataset.lang = lang;

    function showCopyTooltip() {
      const tooltip = document.createElement('div');
      tooltip.className = 'code-block-tooltip';
      tooltip.textContent = 'Copy';
      document.body.appendChild(tooltip);
      const rect = copyBtn.getBoundingClientRect();
      const th = tooltip.offsetHeight;
      tooltip.style.top = (rect.top - 5 - th) + 'px';
      tooltip.style.left = (rect.left + rect.width / 2) + 'px';
      tooltip.style.transform = 'translateX(-50%)';
      requestAnimationFrame(() => tooltip.classList.add('code-block-tooltip--visible'));
      copyBtn._tooltip = tooltip;
    }

    function hideCopyTooltip() {
      if (copyBtn._tooltip) {
        copyBtn._tooltip.remove();
        copyBtn._tooltip = null;
      }
    }

    copyBtn.addEventListener('mouseenter', showCopyTooltip);
    copyBtn.addEventListener('mouseleave', hideCopyTooltip);
    actions.appendChild(copyBtn);

    if (editor?.isEditable && block) {
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'code-delete-btn';
      deleteBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="1em" height="1em"><path d="M17 6H22V8H20V21C20 21.5523 19.5523 22 19 22H5C4.44772 22 4 21.5523 4 21V8H2V6H7V3C7 2.44772 7.44772 2 8 2H16C16.5523 2 17 2.44772 17 3V6ZM18 8H6V20H18V8ZM9 4V6H15V4H9Z"/></svg>';
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        editor.removeBlocks([block]);
      });

      function showTooltip() {
        const tooltip = document.createElement('div');
        tooltip.className = 'code-block-tooltip';
        tooltip.textContent = 'Delete';
        document.body.appendChild(tooltip);
        const rect = deleteBtn.getBoundingClientRect();
        const th = tooltip.offsetHeight;
        tooltip.style.top = (rect.top - 5 - th) + 'px';
        tooltip.style.left = (rect.left + rect.width / 2) + 'px';
        tooltip.style.transform = 'translateX(-50%)';
        requestAnimationFrame(() => tooltip.classList.add('code-block-tooltip--visible'));
        deleteBtn._tooltip = tooltip;
      }

      function hideTooltip() {
        if (deleteBtn._tooltip) {
          deleteBtn._tooltip.remove();
          deleteBtn._tooltip = null;
        }
      }

      deleteBtn.addEventListener('mouseenter', showTooltip);
      deleteBtn.addEventListener('mouseleave', hideTooltip);
      actions.appendChild(deleteBtn);
    }

    dom.appendChild(actions);
  }

  spec.implementation.render = (block, editor) => {
    const result = originalRender(block, editor);

    const selectEl = result.dom.querySelector('select');
    const codeEl = result.dom.querySelector('code');
    const lang = selectEl?.value
        || Array.from(codeEl?.classList || []).find((c) => c.startsWith('language-'))?.replace('language-', '')
        || '';
    ensureHeaderButtons(result.dom, lang, block, editor);

    if (!editor.isEditable) {
      const select = result.dom.querySelector('select');
      if (select) {
        select.style.display = 'none';
        const lang = select.options[select.selectedIndex]?.text || '';
        const container = document.createElement('div');
        container.className = 'code-block-lang-selector';
        const label = document.createElement('span');
        label.className = 'code-block-lang-trigger';
        label.dataset.readonly = '';
        label.textContent = lang;
        container.appendChild(label);
        result.dom.querySelector('[contenteditable="false"]')?.appendChild(container);
      }
      return result;
    }

    const wrapperDiv = result.dom.querySelector('[contenteditable="false"]');
    if (wrapperDiv) {
      const select = wrapperDiv.querySelector('select');
      if (select && select.options.length > 0) {
        if (widgetInstance) {
          widgetInstance._closeDropdown?.();
        }
        widgetInstance = createLanguageSelectorWidget(select, block, editor);
      }
    }

    return result;
  };

  return spec;
}
