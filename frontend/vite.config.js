import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.VITE_API_PROXY || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/search': { target: apiTarget, changeOrigin: true },
      '/document': { target: apiTarget, changeOrigin: true },
    },
  },
})