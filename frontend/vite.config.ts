import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Backend host for the dev proxy. Override with VITE_BACKEND_URL if the
// FastAPI app is not running on the default local port.
const backendUrl = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: backendUrl, changeOrigin: true },
      '/auth': { target: backendUrl, changeOrigin: true },
      '/report': { target: backendUrl, changeOrigin: true },
    },
  },
});
