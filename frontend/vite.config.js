import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Use '/grid-app/' for GitHub Pages, '/' for Docker/local
const base = process.env.VITE_BASE_URL || (process.env.NODE_ENV === 'production' ? '/grid-app/' : '/');

// https://vitejs.dev/config/
export default defineConfig({
    base,
    plugins: [react()],
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ''),
            },
            '/graphql': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/stream': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: 'dist',
    },
});
