const blockDomMap = new Map();
const blockIdMap = new Map();

let sharedOverlay = null;
let lastActiveId = null;
let editingActive = false;
let lastMousedownTime = 0;
let lastMousedownId = null;
let selectionFrameId = null;
let copyBuffer = null;
let suppressOverlay = false;
let editorResizeObserver = null;
let suppressOnSelectionChange = false;

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
  const contentType = blockEl.getAttribute('data-content-type');
  const isMedia = contentType === 'image' || contentType === 'video'
                  || block.type === 'image' || block.type === 'video';
  const wasRegistered = blockEl.dataset.blockId === block.id;
  blockEl.dataset.blockId = block.id;
  blockIdMap.set(block.id, block);
  if (isMedia) {
    blockDomMap.delete(block.id);
    return;
  }
  ensureOverlay();
  blockEl.classList.add('block-wrapper');
  blockDomMap.set(block.id, blockEl);
  initListeners(editor);
}

function applyBlockOutline(id, editing) {
  const el = blockDomMap.get(id);
  if (!el) return;
  lastActiveId = id;
  el.classList.add('block-selected');
  el.classList.toggle('bn-editing', editing);
  // Remove PM native selection outline from descendants (e.g. video→codeBlock transition)
  el.querySelectorAll('.ProseMirror-selectednode').forEach((child) => child.classList.remove('ProseMirror-selectednode'));
  positionOverlay(el, editing);
}

function clearBlockSelection() {
  if (selectionFrameId) {
    cancelAnimationFrame(selectionFrameId);
    selectionFrameId = null;
  }
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
  lastMousedownTime = 0;
  lastMousedownId = null;
  suppressOnSelectionChange = false;
}

let mousedownHandler = null;
let clickHandler = null;
let deleteKeyHandler = null;
let shortKeyHandler = null;
let scrollHandler = null;
let resizeHandler = null;
let beforeinputHandler = null;
let ctrlAHandler = null;
let copyPasteHandler = null;
let pasteHandler = null;
let selectionUnsubscribe = null;

function removeDocumentListeners() {
  if (mousedownHandler) document.removeEventListener('mousedown', mousedownHandler, true);
  if (clickHandler) document.removeEventListener('click', clickHandler, true);
  if (deleteKeyHandler) document.removeEventListener('keydown', deleteKeyHandler, true);
  if (shortKeyHandler) document.removeEventListener('keydown', shortKeyHandler, true);
  if (scrollHandler) window.removeEventListener('scroll', scrollHandler, true);
  if (resizeHandler) window.removeEventListener('resize', resizeHandler);
  if (beforeinputHandler) document.removeEventListener('beforeinput', beforeinputHandler, true);
  if (ctrlAHandler) document.removeEventListener('keydown', ctrlAHandler, true);
  if (copyPasteHandler) document.removeEventListener('keydown', copyPasteHandler, true);
  if (pasteHandler) document.removeEventListener('paste', pasteHandler, true);
  if (selectionUnsubscribe) selectionUnsubscribe();
  mousedownHandler = null;
  clickHandler = null;
  deleteKeyHandler = null;
  shortKeyHandler = null;
  scrollHandler = null;
  resizeHandler = null;
  beforeinputHandler = null;
  ctrlAHandler = null;
  copyPasteHandler = null;
  pasteHandler = null;
  selectionUnsubscribe = null;
}

function repositionOverlay() {
  if (!lastActiveId) return;
  if (suppressOnSelectionChange) {
    return;
  }
  const el = blockDomMap.get(lastActiveId);
  if (el) positionOverlay(el, editingActive);
}

function initListeners(editor) {
  if (clickHandler) return;

  // Single ResizeObserver on editor root captures all layout shifts (Shiki, font, PM re-render)
  const editorRoot = editor.dom?.closest('.bn-editor') || editor.dom || document.querySelector('.bn-editor');
  if (editorRoot && !editorResizeObserver) {
    editorResizeObserver = new ResizeObserver(() => {
      repositionOverlay();
    });
    editorResizeObserver.observe(editorRoot);
  }

  mousedownHandler = (e) => {
    suppressOnSelectionChange = false;
    // Remove stale .ProseMirror-selectednode only if click target differs
    const staleNodes = document.querySelectorAll('.ProseMirror-selectednode');
    if (staleNodes.length > 0) {
      const newBlockEl = e.target.closest('[data-block-id]');
      const clickIsOnOldBlock = staleNodes.length === 1 && newBlockEl && newBlockEl === staleNodes[0];
      if (!clickIsOnOldBlock) {
        staleNodes.forEach((el) => el.classList.remove('ProseMirror-selectednode'));
      }
    }

    if (editingActive) return;

    // Fallback for blockIdMap-only blocks (images/videos)
    const blockEl = e.target.closest('[data-block-id]');
    if (blockEl) {
      const id = blockEl.dataset.blockId;
      if (id && blockIdMap.has(id) && !blockDomMap.has(id)) {
        if (lastActiveId && lastActiveId !== id) {
          const prev = blockDomMap.get(lastActiveId);
          if (prev) prev.classList.remove('block-selected', 'bn-editing');
        }
        if (sharedOverlay) sharedOverlay.style.display = 'none';
        lastActiveId = id;
        editingActive = false;
        return;
      }
    }

    const wrapper = e.target.closest('.block-wrapper');
    if (!wrapper) return;
    const id = wrapper.dataset.blockId;
    if (!id || !blockDomMap.has(id)) return;
    e.preventDefault();
    e.stopPropagation();

    const sel = window.getSelection();
    if (sel && !sel.isCollapsed) sel.removeAllRanges();

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
    suppressOnSelectionChange = false;
    if (!e.target.closest('.ProseMirror')) {
      document.querySelectorAll('.ProseMirror-selectednode').forEach((el) => {
        el.classList.remove('ProseMirror-selectednode');
      });
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

  beforeinputHandler = (e) => {
    if (editingActive) return;
    if (!lastActiveId) return;
    e.preventDefault();
    e.stopPropagation();
  };
  document.addEventListener('beforeinput', beforeinputHandler, true);

  ctrlAHandler = (e) => {
    if (!(e.ctrlKey || e.metaKey) || e.key !== 'a') return;
    if (!lastActiveId) return;
    if (editingActive) return;
    e.preventDefault();
    e.stopPropagation();
    clearBlockSelection();
  };
  document.addEventListener('keydown', ctrlAHandler, true);

  copyPasteHandler = (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (!mod) return;
    if (editingActive) return;

    if (e.key === 'c') {
      if (!lastActiveId) return;
      if (suppressOnSelectionChange) return;  // no copy after paste (no overlay)
      const block = blockIdMap.get(lastActiveId);
      if (!block) return;
      copyBuffer = { type: block.type, props: { ...block.props }, content: block.content };
      e.preventDefault();
      e.stopPropagation();
    }
  };
  document.addEventListener('keydown', copyPasteHandler, true);

  pasteHandler = (e) => {
    if (!lastActiveId) return;
    if (editingActive) return;
    const block = blockIdMap.get(lastActiveId);
    if (!block) return;
    e.preventDefault();
    e.stopPropagation();

    let pasteContent;
    if (copyBuffer) {
      pasteContent = copyBuffer;
    } else {
      const text = e.clipboardData?.getData('text/plain') || '';
      if (!text) return;
      pasteContent = { type: 'paragraph', content: text };
    }

    const targetId = lastActiveId;
    editor.updateBlock(block, { type: pasteContent.type, props: pasteContent.props, content: pasteContent.content });
    // Clean up PM native .ProseMirror-selectednode from previous block DOM
    document.querySelectorAll('.ProseMirror-selectednode').forEach((el) => el.classList.remove('ProseMirror-selectednode'));
    if (sharedOverlay) {
      sharedOverlay.style.display = 'none';
    }
    // Sync: block-selected class + blur to hide caret immediately
    const targetEl = blockDomMap.get(targetId);
    if (targetEl) {
      lastActiveId = targetId;
      editingActive = false;
      targetEl.classList.add('block-selected');
      suppressOnSelectionChange = true;
      editor.blur();
    }
    // Async: restore PM selection after Shiki layout settle (no overlay, suppressOnSelectionChange blocks onSelectionChange until click)
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (targetId && blockDomMap.has(targetId)) {
          editor.setTextCursorPosition(targetId);
          lastActiveId = targetId;
          editingActive = false;
          // suppressOnSelectionChange stays true — user click in mousedownHandler resets it + shows overlay
        }
      });
    });
  };
  document.addEventListener('paste', pasteHandler, true);

  scrollHandler = () => repositionOverlay();
  window.addEventListener('scroll', scrollHandler, true);

  resizeHandler = () => repositionOverlay();
  window.addEventListener('resize', resizeHandler);

  selectionUnsubscribe = editor.onSelectionChange(() => {
    // GUARD: suppressOnSelectionChange active → preserve overlay after paste blur
    if (suppressOnSelectionChange && lastActiveId && blockDomMap.has(lastActiveId)) {
      return;
    }

    // --- SYNC: update lastActiveId immediately (before rAF) ---
    let activeId = null;

    // PRIORITY: .ProseMirror-selectednode detects image/video node selections
    const pmSelectedNodes = document.querySelectorAll('.ProseMirror-selectednode');
    if (pmSelectedNodes.length > 0) {
      pmSelectedNodes.forEach((node) => {
        const blockEl = node.closest('[data-block-id]');
        if (blockEl) {
          const id = blockEl.dataset.blockId;
          if (id && blockIdMap.has(id) && !blockDomMap.has(id)) {
            activeId = id;
          }
        }
      });
    }

    // Always get cursor position for stale detection
    let cursorId = null;
    let cursorThrew = false;
    try {
      const pos = editor.getTextCursorPosition();
      cursorId = pos?.block?.id || null;
    } catch (e) {
      cursorThrew = true;
    }


    // Stale detection: DOM node selection differs from cursor position
    if (activeId && !cursorThrew && cursorId && cursorId !== activeId) {
      document.querySelectorAll('.ProseMirror-selectednode').forEach((el) => el.classList.remove('ProseMirror-selectednode'));
      activeId = cursorId;
    }

    // FALLBACK: use cursor position if no DOM node selection
    if (!activeId) {
      activeId = cursorId;
    }

    // Preserve image/video selection set by mousedown (PM cursor may be elsewhere)
    if (lastActiveId && blockIdMap.has(lastActiveId) && !blockDomMap.has(lastActiveId)) {
      if (activeId && activeId !== lastActiveId) {
        return;
      }
    }

    const hasBlock = blockDomMap.has(activeId);
    if (!hasBlock) {
      if (activeId && blockIdMap.has(activeId)) {
        if (suppressOverlay) { suppressOverlay = false; return; }
        if (lastActiveId && lastActiveId !== activeId) {
          const el = blockDomMap.get(lastActiveId);
          if (el) el.classList.remove('block-selected', 'bn-editing');
        }
        lastActiveId = activeId;
        editingActive = false;
        if (sharedOverlay) {
          sharedOverlay.style.display = 'none';
          sharedOverlay.classList.remove('code-block-selection-overlay--editing');
        }
        return;
      }
      if (activeId !== lastActiveId) {
        if (lastActiveId) {
          const el = blockDomMap.get(lastActiveId);
          if (el) el.classList.remove('block-selected', 'bn-editing');
        }
        editingActive = false;
        if (sharedOverlay) {
          sharedOverlay.style.display = 'none';
          sharedOverlay.classList.remove('code-block-selection-overlay--editing');
        }
      }
      lastActiveId = activeId;
      if (suppressOverlay) suppressOverlay = false;
      return;
    }

    if (activeId !== lastActiveId) editingActive = false;
    lastActiveId = activeId;

    // --- ASYNC (rAF): overlay positioning only ---
    if (selectionFrameId) cancelAnimationFrame(selectionFrameId);
    selectionFrameId = requestAnimationFrame(() => {
      selectionFrameId = null;
      // Guard: suppressOnSelectionChange active (paste) — rAF was queued before flag was set
      if (suppressOnSelectionChange && lastActiveId && blockDomMap.has(lastActiveId)) {
        return;
      }
      const sel = window.getSelection();
      const isTextSelection = sel && !sel.isCollapsed;
      if (isTextSelection) {
        if (sharedOverlay) {
          sharedOverlay.style.display = 'none';
          sharedOverlay.classList.remove('code-block-selection-overlay--editing');
        }
        return;
      }
      // Don't show overlay when PM has a node selection (image/video)
      const hasNodeSelection = document.querySelectorAll('.ProseMirror-selectednode').length > 0;
      if (hasNodeSelection) {
        if (sharedOverlay) {
          sharedOverlay.style.display = 'none';
          sharedOverlay.classList.remove('code-block-selection-overlay--editing');
        }
        return;
      }
      if (suppressOverlay) {
        suppressOverlay = false;
        editingActive = false;
        applyBlockOutline(activeId, false);
        return;
      }
      applyBlockOutline(activeId, editingActive);
    });
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
  if (editorResizeObserver) {
    editorResizeObserver.disconnect();
    editorResizeObserver = null;
  }
  blockDomMap.clear();
  blockIdMap.clear();
  removeDocumentListeners();
  lastMousedownTime = 0;
  lastMousedownId = null;
  copyBuffer = null;
  suppressOverlay = false;
  suppressOnSelectionChange = false;
}
