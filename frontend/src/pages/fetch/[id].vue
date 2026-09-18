<script lang="ts" setup>
import {useRoute} from 'vue-router'
import {useTaskQuery} from '../../composables/useTasks'
import {useLiveEvents} from '../../composables/useLiveEvents'
import {useQueryClient} from '@tanstack/vue-query'
import type {Task} from '../../api/tasks'
import {computed, watch} from "vue"
import {StepperItem} from "@nuxt/ui";
import {useTitle} from "@vueuse/core";

const route = useRoute<'/fetch/[id]'>()
const {data, isLoading, error} = useTaskQuery(() => route.params.id)

const queryClient = useQueryClient()
const {data: liveData, event: liveEvent} = useLiveEvents()

watch([liveData, liveEvent], ([raw, type]) => {
  if (!raw || (type !== 'metadata' && type !== 'fetch_updated')) return
  const payload = JSON.parse(raw)
  if (payload.fetch_id !== route.params.id) return

  const key = ['task', route.params.id]
  if (type === 'metadata') {
    queryClient.setQueryData<Task>(key, (old) => old && {...old, meta: JSON.parse(payload.meta)})
  } else {
    queryClient.setQueryData<Task>(key, (old) => old && {
      ...old,
      status: payload.state,
      output_path: payload.path ?? old.output_path
    })
  }
})

const items = computed<StepperItem[]>(() => [
  {
    title: 'Created',
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
      title: 'Failed',
      description: 'The fetch failed. Check the logs.',
      icon: 'pepicons-pop:exclamation',
      value: 'failed'
    }
    : {
      title: 'Complete',
      description: 'The fetch is complete.',
      icon: 'pepicons-pop:checkmark',
      value: 'success'
    },
])

const timelineColor = computed(() => data.value?.status === 'failed' ? 'error' : 'success')

const title = useTitle()
if (data.value?.id) {
  title.value = "Slurp " + data.value?.id.slice(-4)
}

</script>

<template>
  <p v-if="isLoading">
    <UContainer>
      <USkeleton class="h-40 w-full" />
      <USkeleton class="h-40 w-full" />
      <USeparator class="h-40 w-full" />
      <USkeleton class="h-100 w-100" />
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
    <UContainer class="flex flex-col items-center">
      <UContainer class="flex items-center flex-col md:flex-row justify-center gap-10">
        <img
          :src="data.meta.thumbnail_url"
          class="block-40 rounded-lg"
        >
        <FetchCard
          :task="data"
          extended
        />
      </UContainer>
      <UStepper
        :color="timelineColor"
        :items="items"
        :model-value="data.status"
        class="w-full pt-5"
        disabled
        orientation="horizontal"
      />
    </UContainer>
    <USeparator class="py-5" />
    <UContainer>
      <h2 class="text-4xl font-bold pb-2">
        Fetch Log
      </h2>
      <FetchEventLog
        v-if="!data.purged"
        :id="data.id"
        :live="!['success', 'failed'].includes(data.status)"
      />
      <UAlert
        v-else
        color="info"
        description="The Fetch Log for this Fetch has been purged after expiry."
        icon="material-symbols:bomb"
      />
    </UContainer>
  </div>
</template>
