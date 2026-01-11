import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Use GitHub Pages base path when deployed (falls back to repo name if not provided)
const base = process.env.PUBLIC_URL || '/grid-app/';

// https://vitejs.dev/config/
export default defineConfig({
    base,
    plugins: [react()],
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://backend:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ''),
            },
            '/graphql': {
                target: 'http://backend:8000',
                changeOrigin: true,
            },
            '/stream': {
                target: 'http://backend:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: 'dist',
    },
});
