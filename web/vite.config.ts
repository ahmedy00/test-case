import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    watch: {
      // Polling so file changes propagate from a host bind mount on Windows/macOS.
      usePolling: true,
    },
  },
});
