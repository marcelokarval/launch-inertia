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
  base: '/static/landing/',
  server: {
    host: '0.0.0.0',
    port: 3345,
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
      port: 3345,
      protocol: 'ws',
    },
    watch: {
      ignored: ['**/node_modules/**', '**/.venv/**', '**/.git/**'],
    },
  },
  build: {
    outDir: '../../src/static/landing',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: resolve(__dirname, 'src/main.tsx'),
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        manualChunks: {
          'vendor-inertia': ['react', 'react-dom', '@inertiajs/react', '@inertiajs/core'],
          'vendor-stripe': ['@stripe/stripe-js', '@stripe/react-stripe-js'],
          'vendor-phone': ['react-international-phone'],
        },
      },
    },
  },
})
