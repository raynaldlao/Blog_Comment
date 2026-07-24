export function _(key) {
  try {
    const el = document.getElementById('app-translations');
    const dict = el ? JSON.parse(el.textContent) : {};
    if (dict[key] !== undefined) return dict[key];
  } catch {}
  return key;
}
