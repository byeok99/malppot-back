// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5174,      // 원하는 포트
        strictPort: true // 5174가 이미 사용 중이면 실패하고 종료
    },
    resolve: {
        alias: {
            pages: path.resolve(__dirname, './src/pages'),
            utils: path.resolve(__dirname, './src/utils'),
            assets: path.resolve(__dirname, './src/assets'),
            components: path.resolve(__dirname, './src/components'),
            store: path.resolve(__dirname, './src/store'),
            apis: path.resolve(__dirname, './src/apis'),
            config: path.resolve(__dirname, './src/config'),
            types: path.resolve(__dirname, './src/types'),
            hooks: path.resolve(__dirname, './src/hooks')
        },
    },
});