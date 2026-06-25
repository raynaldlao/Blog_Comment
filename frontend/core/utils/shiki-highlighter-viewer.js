// Adapted from shiki-highlighter-editor.js — lazy-loaded core + per-language chunks

const plaintextLang = {
  name: 'plaintext',
  scopeName: 'text.plain',
  patterns: [],
  repository: {},
};

const ALL_THEMES = {
  'github-dark': () => import('@shikijs/themes/github-dark').then(m => m.default || m),
  'github-light': () => import('@shikijs/themes/github-light').then(m => m.default || m),
};

async function createHighlighter(options) {
  const [{ createBundledHighlighter }, { createJavaScriptRegexEngine }] = await Promise.all([
    import('@shikijs/core'),
    import('@shikijs/engine-javascript'),
  ]);

  const highlighterFactory = createBundledHighlighter({
    langs: {
      'plaintext': () => Promise.resolve(plaintextLang),
  "c": () => import('@shikijs/langs-precompiled/c').then(m => m.default || m),
  "cpp": () => import('@shikijs/langs-precompiled/cpp').then(m => m.default || m),
  "csharp": () => import('@shikijs/langs-precompiled/csharp').then(m => m.default || m),
  "css": () => import('@shikijs/langs-precompiled/css').then(m => m.default || m),
  "diff": () => import('@shikijs/langs-precompiled/diff').then(m => m.default || m),
  "docker": () => import('@shikijs/langs-precompiled/docker').then(m => m.default || m),
  "go": () => import('@shikijs/langs-precompiled/go').then(m => m.default || m),
  "graphql": () => import('@shikijs/langs-precompiled/graphql').then(m => m.default || m),
  "html": () => import('@shikijs/langs-precompiled/html').then(m => m.default || m),
  "java": () => import('@shikijs/langs-precompiled/java').then(m => m.default || m),
  "javascript": () => import('@shikijs/langs-precompiled/javascript').then(m => m.default || m),
  "json": () => import('@shikijs/langs-precompiled/json').then(m => m.default || m),
  "jsonc": () => import('@shikijs/langs-precompiled/jsonc').then(m => m.default || m),
  "jsx": () => import('@shikijs/langs-precompiled/jsx').then(m => m.default || m),
  "kotlin": () => import('@shikijs/langs-precompiled/kotlin').then(m => m.default || m),
  "lua": () => import('@shikijs/langs-precompiled/lua').then(m => m.default || m),
  "make": () => import('@shikijs/langs-precompiled/make').then(m => m.default || m),
  "markdown": () => import('@shikijs/langs-precompiled/markdown').then(m => m.default || m),
  "php": () => import('@shikijs/langs-precompiled/php').then(m => m.default || m),
  "powershell": () => import('@shikijs/langs-precompiled/powershell').then(m => m.default || m),
  "python": () => import('@shikijs/langs-precompiled/python').then(m => m.default || m),
  "r": () => import('@shikijs/langs-precompiled/r').then(m => m.default || m),
  "ruby": () => import('@shikijs/langs-precompiled/ruby').then(m => m.default || m),
  "rust": () => import('@shikijs/langs-precompiled/rust').then(m => m.default || m),
  "scss": () => import('@shikijs/langs-precompiled/scss').then(m => m.default || m),
  "shellscript": () => import('@shikijs/langs-precompiled/shellscript').then(m => m.default || m),
  "shellsession": () => import('@shikijs/langs-precompiled/shellsession').then(m => m.default || m),
  "sql": () => import('@shikijs/langs-precompiled/sql').then(m => m.default || m),
  "swift": () => import('@shikijs/langs-precompiled/swift').then(m => m.default || m),
  "terraform": () => import('@shikijs/langs-precompiled/terraform').then(m => m.default || m),
  "toml": () => import('@shikijs/langs-precompiled/toml').then(m => m.default || m),
  "tsx": () => import('@shikijs/langs-precompiled/tsx').then(m => m.default || m),
  "typescript": () => import('@shikijs/langs-precompiled/typescript').then(m => m.default || m),
  "xml": () => import('@shikijs/langs-precompiled/xml').then(m => m.default || m),
  "yaml": () => import('@shikijs/langs-precompiled/yaml').then(m => m.default || m),
    },
    themes: ALL_THEMES,
    engine: () => createJavaScriptRegexEngine(),
  });

  const highlighter = await highlighterFactory({
    ...options,
    themes: ['github-dark', 'github-light'],
  });
  return highlighter;
}

export default createHighlighter;
