<script lang="ts" setup>
import {computed} from 'vue'
import {useHead} from '@unhead/vue'
import {useColorMode, useFavicon} from '@vueuse/core'
import {VueQueryDevtools} from '@tanstack/vue-query-devtools'
import AuthorLogo from "./components/AuthorLogo.vue";
import {useLiveEvents} from "./composables/useLiveEvents";
import {useNotifier} from "./composables/useNotifier.ts";

import favicon from "./assets/img/favicon.ico";

const {status: liveEventsStatus} = useLiveEvents()
useNotifier()

const liveEventsStatusText = computed(() => ({
  OPEN: 'Live!',
  CONNECTING: 'Connecting…',
  CLOSED: 'No Connection'
})[liveEventsStatus.value])

const liveEventsStatusColor = computed(() => ({
  OPEN: 'success',
  CONNECTING: 'warning',
  CLOSED: 'error'
} as const)[liveEventsStatus.value])

const colorMode = useColorMode()
const isDev = import.meta.env.DEV
const themeColor = computed(() => colorMode.value === 'dark' ? '#18181b' : '#ffffff')

const appIcon = import.meta.env.VITE_APP_ICON ? import.meta.env.VITE_APP_ICON : "simple-icons:cbs"
const appCopyright = import.meta.env.VITE_APP_COPYRIGHT ? import.meta.env.VITE_APP_COPYRIGHT : "CBS News"
const appVersion = import.meta.env.DEV ? __APP_COMMIT__ : __APP_VERSION__

useHead({
  meta: [
    {name: 'theme-color', content: themeColor}
  ],
})

const icon = useFavicon()
icon.value = favicon
</script>

<template>
  <Suspense>
    <UApp>
      <UHeader :toggle="false">
        <template #left>
          <RouterLink
            class="focus-visible:outline-3 outline-primary/25 rounded-md p-1 -ms-1"
            to="/"
          >
            <AppLogo class="w-auto h-6 shrink-0 text-2xl"/>
          </RouterLink>
        </template>

        <template #right>
          <UBadge
            :color="liveEventsStatusColor"
            :label="liveEventsStatusText"
            :ui="{
              base: '-right-2'
            }"
          />
          <UColorModeButton/>
        </template>
      </UHeader>

      <UMain class="pt-5">
        <RouterView/>
      </UMain>

      <USeparator :icon="appIcon"/>

      <UFooter>
        <template #left>
          <p class="text-sm text-muted">
            © {{ appCopyright }} {{ new Date().getFullYear() }}
          </p>
          <USeparator
            class="h-3"
            orientation="vertical"
          />
          <p class="text-sm text-muted flex flex-nowrap items-center">
            A <a href="https://duck.me.uk">
            <AuthorLogo class="flex-1 h-3 px-1"/>
          </a> project
          </p>
        </template>

        <template #right>
          <UBadge
            class="font-mono"
            color="neutral"
            variant="soft"
          >
            <UIcon name="material-symbols:package-2"/>
            {{ appVersion }}
          </UBadge>
          <UButton
            aria-label="GitHub"
            color="neutral"
            icon="simple-icons:github"
            target="_blank"
            to="https://github.com/duckfullstop/slurp"
            variant="ghost"
          />
        </template>
      </UFooter>
    </UApp>
  </Suspense>
  <VueQueryDevtools v-if="isDev"/>
</template>
