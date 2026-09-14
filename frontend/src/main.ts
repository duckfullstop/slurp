import './assets/css/main.css'

import {createApp} from 'vue'
import {createRouter, createWebHistory} from 'vue-router'
import {handleHotUpdate, routes} from 'vue-router/auto-routes'
import {createHead} from '@unhead/vue/client'
import ui from '@nuxt/ui/vue-plugin'
import {QueryClient, VueQueryPlugin} from '@tanstack/vue-query'

import App from './App.vue'

const app = createApp(App)

const head = createHead()
const router = createRouter({
  routes,
  history: createWebHistory()
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000
    }
  }
})

app.use(head)
app.use(router)
app.use(ui)
app.use(VueQueryPlugin, {queryClient})

app.mount('#app')

if (import.meta.hot) {
  handleHotUpdate(router)
}
