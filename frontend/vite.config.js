import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/dist/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: 'core/entry.jsx',
      output: {
        manualChunks(id) {
          if (id.includes('@shikijs/langs-precompiled')) return 'shiki-langs';
          if (id.includes('node_modules')) {
            if (id.includes('@blocknote') || id.includes('@mantine') || id.includes('react') || id.includes('react-dom')) return 'vendor';
            if (id.includes('@shikijs')) return 'shiki';
          }
        },
      },
    },
  },
  server: {
    port: 5173,
  },
});
