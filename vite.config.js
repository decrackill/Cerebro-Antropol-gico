import { defineConfig } from 'vite'

export default defineConfig({
  root: 'frontend',
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': 'https://cerebro-antropologico.pages.dev'
    }
  }
})
