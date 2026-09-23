import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueRouter from 'vue-router/vite'
import ui from '@nuxt/ui/vite'
import * as child from 'child_process'
import packageConfig from './package.json' with {type: 'json'}

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
          primary: 'red',
          warning: 'amber',
          error: 'rose',
          neutral: 'stone'
        },
        icons: {
          arrowDown: 'i-material-symbols-arrow-downward-rounded',
          arrowLeft: 'i-material-symbols-arrow-back-rounded',
          arrowRight: 'i-material-symbols-arrow-forward-rounded',
          arrowUp: 'i-material-symbols-arrow-upward-rounded',
          caution: 'i-material-symbols-error-outline-rounded',
          check: 'i-material-symbols-check-rounded',
          chevronDoubleLeft: 'i-material-symbols-keyboard-double-arrow-left-rounded',
          chevronDoubleRight: 'i-material-symbols-keyboard-double-arrow-right-rounded',
          chevronDown: 'i-material-symbols-keyboard-arrow-down-rounded',
          chevronLeft: 'i-material-symbols-chevron-left-rounded',
          chevronRight: 'i-material-symbols-chevron-right-rounded',
          chevronUp: 'i-material-symbols-keyboard-arrow-up-rounded',
          close: 'i-material-symbols-close-rounded',
          copy: 'i-material-symbols-content-copy-outline-rounded',
          copyCheck: 'i-material-symbols-inventory-rounded',
          dark: 'i-material-symbols-dark-mode-outline-rounded',
          drag: 'i-material-symbols-drag-indicator',
          ellipsis: 'i-material-symbols-more-horiz',
          error: 'i-material-symbols-cancel-outline-rounded',
          external: 'i-material-symbols-arrow-outward-rounded',
          eye: 'i-material-symbols-visibility-outline-rounded',
          eyeOff: 'i-material-symbols-visibility-off-outline-rounded',
          file: 'i-material-symbols-description-outline-rounded',
          folder: 'i-material-symbols-folder-outline-rounded',
          folderOpen: 'i-material-symbols-folder-open-outline-rounded',
          hash: 'i-material-symbols-tag-rounded',
          info: 'i-material-symbols-info-outline-rounded',
          light: 'i-material-symbols:light-mode-outline-rounded',
          loading: 'i-material-symbols-progress-activity',
          menu: 'i-material-symbols-menu-rounded',
          minus: 'i-material-symbols-remove-rounded',
          panelClose: 'i-material-symbols-left-panel-close-outline-rounded',
          panelOpen: 'i-material-symbols-left-panel-open-outline-rounded',
          plus: 'i-material-symbols-add-rounded',
          reload: 'i-material-symbols-refresh-rounded',
          search: 'i-material-symbols-search-rounded',
          stop: 'i-material-symbols-stop-outline-rounded',
          star: 'i-material-symbols-star-outline-rounded',
          success: 'i-material-symbols-check-circle-outline-rounded',
          system: 'i-material-symbols-desktop-windows-outline-rounded',
          tip: 'i-material-symbols-lightbulb-outline-rounded',
          upload: 'i-material-symbols-upload-rounded',
          warning: 'i-material-symbols-warning-outline-rounded'
        }
      }
    })
  ]
})
