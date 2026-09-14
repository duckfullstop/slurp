<script lang="ts" setup>
import {useTasksQuery} from '../composables/useTasks'

const {data, isLoading, error} = useTasksQuery()

</script>

<template>
  <UPageSection>
    <p v-if="isLoading">
      Loading...
    </p>
    <p v-else-if="error">
      Error: {{ error.message }}
    </p>
    <UPageGrid v-else>
      <FetchCard v-for="task in data" v-bind="task"/>
    </UPageGrid>
  </UPageSection>
</template>
