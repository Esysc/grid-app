import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Use '/' for Docker, fallback to '/grid-app/' for GitHub Pages
const base = process.env.VITE_BASE_URL || '/';

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
