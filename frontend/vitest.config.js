import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'happy-dom',
    include: ['core/__tests__/**/*.test.{js,jsx}'],
  },
});
