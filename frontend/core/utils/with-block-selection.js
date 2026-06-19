const blockDomMap = new Map();
const blockIdMap = new Map();

let sharedOverlay = null;
let lastActiveId = null;
let editingActive = false;
let lastMousedownTime = 0;
let lastMousedownId = null;

function ensureOverlay() {
  if (!sharedOverlay) {
    sharedOverlay = document.createElement('div');
    sharedOverlay.className = 'code-block-selection-overlay--external';
    sharedOverlay.style.cssText = 'position:fixed;pointer-events:none;z-index:1000;display:none;';
    document.body.appendChild(sharedOverlay);
  }
  return sharedOverlay;
}

function removeOverlay() {
  if (sharedOverlay) {
    sharedOverlay.remove();
    sharedOverlay = null;
  }
}

function positionOverlay(el, editing) {
  const overlay = ensureOverlay();
  const rect = el.getBoundingClientRect();
  const isCodeBlock = el.closest('.bn-block-content[data-content-type="codeBlock"]') !== null;
  const gap = isCodeBlock ? 0 : 6;
  overlay.style.left = rect.left + 'px';
  overlay.style.top = (rect.top + gap) + 'px';
  overlay.style.width = rect.width + 'px';
  overlay.style.height = (rect.height - gap * 2) + 'px';
  overlay.classList.toggle('code-block-selection-overlay--editing', editing);
  overlay.style.display = 'block';
}

function registerBlock(dom, block, editor) {
  if (!editor?.isEditable || !block) return;
  const blockEl = dom.closest('.bn-block-content') || dom;
  if (blockEl.dataset.blockId === block.id) return;
  const contentType = blockEl.getAttribute('data-content-type');
  if (contentType === 'image' || contentType === 'video') return;
  ensureOverlay();
  blockEl.classList.add('block-wrapper');
  blockEl.dataset.blockId = block.id;
  blockDomMap.set(block.id, blockEl);
  blockIdMap.set(block.id, block);
  initListeners(editor);
}

function applyBlockOutline(id, editing) {
  const el = blockDomMap.get(id);
  if (!el) return;
  lastActiveId = id;
  el.classList.add('block-selected');
  el.classList.toggle('bn-editing', editing);
  positionOverlay(el, editing);
}

function clearBlockSelection() {
  if (lastActiveId) {
    const el = blockDomMap.get(lastActiveId);
    if (el) el.classList.remove('block-selected', 'bn-editing');
  }
  if (sharedOverlay) {
    sharedOverlay.style.display = 'none';
    sharedOverlay.classList.remove('code-block-selection-overlay--editing');
  }
  lastActiveId = null;
  editingActive = false;
}

let mousedownHandler = null;
let clickHandler = null;
let deleteKeyHandler = null;
let shortKeyHandler = null;
let scrollHandler = null;
let resizeHandler = null;
let selectionUnsubscribe = null;

function removeDocumentListeners() {
  if (mousedownHandler) document.removeEventListener('mousedown', mousedownHandler, true);
  if (clickHandler) document.removeEventListener('click', clickHandler, true);
  if (deleteKeyHandler) document.removeEventListener('keydown', deleteKeyHandler, true);
  if (shortKeyHandler) document.removeEventListener('keydown', shortKeyHandler, true);
  if (scrollHandler) window.removeEventListener('scroll', scrollHandler, true);
  if (resizeHandler) window.removeEventListener('resize', resizeHandler);
  if (selectionUnsubscribe) selectionUnsubscribe();
  mousedownHandler = null;
  clickHandler = null;
  deleteKeyHandler = null;
  shortKeyHandler = null;
  scrollHandler = null;
  resizeHandler = null;
  selectionUnsubscribe = null;
}

function repositionOverlay() {
  if (!lastActiveId) return;
  const el = blockDomMap.get(lastActiveId);
  if (el) positionOverlay(el, editingActive);
}

function initListeners(editor) {
  if (clickHandler) return;

  mousedownHandler = (e) => {
    if (editingActive) return;
    const wrapper = e.target.closest('.block-wrapper');
    if (!wrapper) return;
    const id = wrapper.dataset.blockId;
    if (!id || !blockDomMap.has(id)) return;
    e.preventDefault();
    e.stopPropagation();

    const now = Date.now();
    const isDblClick = (now - lastMousedownTime < 400) && (lastMousedownId === id);

    if (isDblClick) {
      lastMousedownTime = 0;
      lastMousedownId = null;
      editingActive = true;
      applyBlockOutline(id, true);
      editor.focus();
      editor.setTextCursorPosition(id);
      return;
    }

    if (lastActiveId && lastActiveId !== id) {
      const prev = blockDomMap.get(lastActiveId);
      if (prev) prev.classList.remove('block-selected', 'bn-editing');
    }
    lastActiveId = id;
    editingActive = false;
    applyBlockOutline(id, false);
    lastMousedownTime = now;
    lastMousedownId = id;
  };
  document.addEventListener('mousedown', mousedownHandler, true);

  clickHandler = (e) => {
    if (!e.target.closest('.ProseMirror')) {
      clearBlockSelection();
    }
  };
  document.addEventListener('click', clickHandler, true);

  deleteKeyHandler = (e) => {
    if (e.key !== 'Backspace' && e.key !== 'Delete') return;
    if (editingActive) return;
    if (!lastActiveId) return;
    e.preventDefault();
    e.stopPropagation();
    const block = blockIdMap.get(lastActiveId);
    if (!block) return;
    editor.removeBlocks([block]);
    clearBlockSelection();
  };
  document.addEventListener('keydown', deleteKeyHandler, true);

  shortKeyHandler = (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (!mod) return;
    if (e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
      editor.undo();
      return;
    }
    if (e.key === 'y' || (e.key === 'z' && e.shiftKey)) {
      e.preventDefault();
      e.stopPropagation();
      editor.redo();
    }
  };
  document.addEventListener('keydown', shortKeyHandler, true);

  scrollHandler = () => repositionOverlay();
  window.addEventListener('scroll', scrollHandler, true);

  resizeHandler = () => repositionOverlay();
  window.addEventListener('resize', resizeHandler);

  selectionUnsubscribe = editor.onSelectionChange(() => {
    const sel = window.getSelection();
    const isTextSelection = sel && !sel.isCollapsed;
    const pos = editor.getTextCursorPosition();
    const activeId = pos?.block?.id || null;
    const hasBlock = blockDomMap.has(activeId);
    if (!hasBlock) {
      clearBlockSelection();
      return;
    }
    if (isTextSelection) {
      if (sharedOverlay) {
        sharedOverlay.style.display = 'none';
        sharedOverlay.classList.remove('code-block-selection-overlay--editing');
      }
      return;
    }
    if (activeId !== lastActiveId) {
      editingActive = false;
    }
    applyBlockOutline(activeId, editingActive);
  });
}

export function withBlockSelection(spec) {
  const originalRender = spec.implementation.render.bind(spec.implementation);
  spec.implementation.render = (block, editor) => {
    const result = originalRender(block, editor);
    registerBlock(result.dom, block, editor);
    return result;
  };
  return spec;
}

export function resetBlockSelection() {
  clearBlockSelection();
  removeOverlay();
  blockDomMap.clear();
  blockIdMap.clear();
  removeDocumentListeners();
  lastMousedownTime = 0;
  lastMousedownId = null;
}
