import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueRouter from 'vue-router/vite'
import ui from '@nuxt/ui/vite'

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  build: {
    assetsDir: './static',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true
      }
    }
  },
  plugins: [
    vueRouter({
      dts: 'src/route-map.d.ts'
    }),
    vue(),
    ui({
      ui: {
        colors: {
          primary: 'brand',
          neutral: 'zinc'
        }
      }
    })
  ]
})
