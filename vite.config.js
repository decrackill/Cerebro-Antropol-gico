import { defineConfig } from 'vite'
import { readFileSync } from 'fs'

export default defineConfig({
  root: '.',
  server: {
    port: 5173,
    host: true,
  },
  plugins: [
    {
      name: 'api-local',
      configureServer(server) {
        server.middlewares.use('/api/datos', (_req, res) => {
          const datos = readFileSync('public/datos.json', 'utf-8')
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: true, ...JSON.parse(datos) }))
        })
      },
    },
  ],
})
