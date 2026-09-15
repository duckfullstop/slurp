<script lang="ts" setup>
import {useTasksQuery} from '../composables/useTasks'

const {data, isLoading, error} = useTasksQuery()

</script>

<template>
  <UContainer>
    <CreateTaskForm/>
  </UContainer>
  <USeparator class="py-5"/>
  <UContainer>
    <p v-if="isLoading">
      <UPageGrid class="flex-col">
        <USkeleton class="h-40 w-100"/>
        <USkeleton class="h-40 w-100"/>
        <USkeleton class="h-40 w-100"/>
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
    <UPageGrid v-else-if="data" class="flex-col-reverse">
      <div v-for="task in data.slice().reverse()" :key="task.id">
        <RouterLink :to="{name: '/fetch/[id]', params: {id: task.id}}">
          <FetchCard v-bind="task"/>
        </RouterLink>
      </div>

    </UPageGrid>
  </UContainer>
</template>
