import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  base: '/static/',
  server: {
    host: '0.0.0.0',
    port: 3344,
    strictPort: true,
    cors: {
      origin: [
        'http://localhost:8844',
        'http://127.0.0.1:8844',
        'http://0.0.0.0:8844',
      ],
      credentials: true,
    },
    hmr: {
      host: 'localhost',
      port: 3344,
      protocol: 'ws',
    },
    watch: {
      ignored: ['**/node_modules/**', '**/.venv/**', '**/.git/**'],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8844',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../src/static/dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: resolve(__dirname, 'src/main.tsx'),
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-inertia': ['@inertiajs/react', '@inertiajs/core'],
          'vendor-heroui': ['@heroui/react'],
          'vendor-i18n': ['i18next', 'react-i18next', 'i18next-browser-languagedetector', 'i18next-http-backend'],
        },
      },
    },
  },
})
