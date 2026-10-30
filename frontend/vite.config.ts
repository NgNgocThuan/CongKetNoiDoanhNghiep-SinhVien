import { fileURLToPath, URL } from 'node:url'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.BACKEND_PROXY_TARGET || 'http://127.0.0.1:8000'
  return {
    plugins: [react()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy: {
      '/api/v1': { target, changeOrigin: true },
      '/health': { target, changeOrigin: true },
    } },
    test: { include: ['src/**/*.test.{ts,tsx}'], environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], css: false,
      maxWorkers: 2, restoreMocks: true, clearMocks: true },
  }
})
