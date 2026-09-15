import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueRouter from 'vue-router/vite'
import ui from '@nuxt/ui/vite'
import * as child from 'child_process'
import packageConfig from './package.json'

let commitHash: string
try {
  commitHash = child.execSync('git rev-parse --short HEAD').toString().trim().toUpperCase()
} catch (e) {
  console.error(e)
  commitHash = 'GIT?'
}

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  build: {
    assetsDir: './static',
  },
  define: {
    __APP_COMMIT__: JSON.stringify(commitHash),
    // @ts-expect-error version may not exist on package config
    __APP_VERSION__: JSON.stringify(packageConfig.version ? packageConfig.version : 'Unknown'),
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
