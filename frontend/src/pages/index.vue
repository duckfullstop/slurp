<script lang="ts" setup>
import {useTasksQuery} from '../composables/useTasks'
import {useLiveEvents} from '../composables/useLiveEvents'
import {useQueryClient} from '@tanstack/vue-query'
import {watch} from "vue";

const {data, isLoading, error} = useTasksQuery()

const queryClient = useQueryClient()
const {data: liveData, event: liveEvent} = useLiveEvents()

watch([liveData, liveEvent], ([raw, type]) => {
  if (!raw || (type !== 'task_created' && type !== 'fetch_updated')) return
  queryClient.invalidateQueries({queryKey: ['tasks']})
})
</script>

<template>
  <UContainer>
    <CreateTaskForm />
  </UContainer>
  <USeparator class="py-5" />
  <UContainer>
    <p v-if="isLoading">
      <UPageGrid class="flex-col">
        <USkeleton class="h-40 w-100" />
        <USkeleton class="h-40 w-100" />
        <USkeleton class="h-40 w-100" />
      </UPageGrid>
    </p>
    <p v-else-if="error">
      <UAlert
        :description="error.message"
        color="error"
        icon="pepicons-pop:exclamation-circle-filled"
        title="Error loading Fetch Tasks"
        variant="solid"
      />
    </p>
    <div
      v-else-if="data"
      class="relative grid grid-cols-1 sm:grid-cols-2 gap-8 flex-col-reverse"
    >
      <div
        v-for="task in data.slice().reverse()"
        :key="task.id"
      >
        <RouterLink
          :to="{name: '/fetch/[id]', params: {id: task.id}}"
          class="block"
        >
          <FetchCard
            :task="task"
            full-width
          />
        </RouterLink>
      </div>
    </div>
  </UContainer>
</template>
