import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Bind to all interfaces so the hosted preview can reach the dev server.
    host: '0.0.0.0',
    // Allow the preview hostname (and any other host) to load the app.
    allowedHosts: true,
    proxy: {
      // Any request starting with /api is forwarded to the Flask backend.
      // This keeps the frontend code free of hard-coded backend URLs and
      // avoids CORS problems during development.
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
