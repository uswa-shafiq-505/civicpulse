import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// The dev proxy exists ONLY for `npm run dev` on your laptop. In containers, nginx proxies /api
// (see ADR-0002), so the built bundle never contains a backend URL.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } },
  test: { environment: 'jsdom', globals: true, setupFiles: './tests/setup.ts', css: false },
})