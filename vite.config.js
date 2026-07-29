import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': 'https://cerebro-antropologico.pages.dev'
    }
  }
})
