<script lang="ts" setup>
import {computed} from 'vue'
import {useHead} from '@unhead/vue'
import {useColorMode} from '@vueuse/core'
import {VueQueryDevtools} from '@tanstack/vue-query-devtools'

const colorMode = useColorMode()
const isDev = import.meta.env.DEV
const themeColor = computed(() => colorMode.value === 'dark' ? '#18181b' : '#ffffff')

useHead({
  meta: [
    {name: 'theme-color', content: themeColor}
  ]
})
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
            <AppLogo class="w-auto h-6 shrink-0"/>
          </RouterLink>
        </template>

        <template #right>
          <UColorModeButton/>
        </template>
      </UHeader>

      <UMain class="pt-5">
        <RouterView/>
      </UMain>

      <USeparator icon="simple-icons:cbs"/>

      <UFooter>
        <template #left>
          <p class="text-sm text-muted">
            © CBS News {{ new Date().getFullYear() }}
          </p>
          <USeparator class="h-3" orientation="vertical"/>
          <p class="text-sm text-muted">
            A <a href="https://duck.me.uk/contact">technoduck.</a> project
          </p>
        </template>

        <template #right>
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
