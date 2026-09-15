<script lang="ts" setup>
import {useRoute} from 'vue-router'
import {useTaskQuery} from '../../composables/useTasks'
import {TimelineItem} from "@nuxt/ui"
import {computed} from "vue"

const route = useRoute<'/fetch/[id]'>()
const {data, isLoading, error} = useTaskQuery(() => route.params.id)

const items = computed<TimelineItem[]>(() => [
  {
    title: 'Fetch Created',
    description: 'Awaiting assignment to a Worker.',
    icon: 'i-lucide-rocket',
    value: 'created'
  },
  {
    title: 'Fetching',
    description: 'Media is downloaded to the target.',
    icon: 'pepicons-pop:cloud-down',
    value: 'running'
  },
  data.value?.status === 'failed'
    ? {
      title: 'Failed.',
      description: 'The fetch failed. Check the logs.',
      icon: 'pepicons-pop:exclamation',
      value: 'failed'
    }
    : {
      title: 'Complete.',
      description: 'The fetch is complete.',
      icon: 'pepicons-pop:checkmark',
      value: 'success'
    },
])

const timelineColor = computed(() => data.value?.status === 'failed' ? 'error' : 'success')
</script>

<template>
  <p v-if="isLoading">
    <UContainer>
      <USkeleton class="h-40 w-full"/>
      <USkeleton class="h-40 w-full"/>
      <USeparator class="h-40 w-full"/>
      <USkeleton class="h-100 w-100"/>
    </UContainer>
  </p>
  <p v-else-if="error">
    <UAlert
      :description="error.message"
      color="error"
      icon="pepicons-pop:exclamation-circle-filled"
      title="Error loading Fetch"
      variant="solid"
    />
  </p>
  <div v-else-if="data">
    <UContainer>
      <FetchCard :id="data.id" :slug="data.slug" :status="data.status" :ts_created="data.ts_created"
                 :url="data.url" extended/>
      <UTimeline :color="timelineColor" :items="items" :model-value="data.status"
                 class="w-full pt-5" orientation="horizontal"/>
    </UContainer>
    <USeparator class="py-5"/>
    <UContainer>
      <h2 class="text-4xl font-bold pb-2">Fetch Log</h2>
      <FetchEventLog :id="data.id"/>
    </UContainer>
  </div>

</template>
