import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { _ } from '../utils/i18n.js';

function setTranslations(dict) {
  const el = document.createElement('script');
  el.id = 'app-translations';
  el.type = 'application/json';
  el.textContent = JSON.stringify(dict);
  document.body.appendChild(el);
}

describe('i18n _()', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('returns translation when key exists', () => {
    setTranslations({ hello: 'bonjour', bye: 'au revoir' });
    expect(_('hello')).toBe('bonjour');
    expect(_('bye')).toBe('au revoir');
  });

  it('returns key when key not in dictionary', () => {
    setTranslations({ hello: 'bonjour' });
    expect(_('missing')).toBe('missing');
  });

  it('returns key when no translations element exists', () => {
    expect(document.getElementById('app-translations')).toBeNull();
    expect(_('hello')).toBe('hello');
  });

  it('returns key when translations JSON is malformed', () => {
    const el = document.createElement('script');
    el.id = 'app-translations';
    el.type = 'application/json';
    el.textContent = '{broken json}';
    document.body.appendChild(el);
    expect(_('hello')).toBe('hello');
  });

  it('returns key when dictionary is empty', () => {
    setTranslations({});
    expect(_('anything')).toBe('anything');
  });
});
