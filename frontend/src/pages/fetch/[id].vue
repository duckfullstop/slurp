<script lang="ts" setup>
import {useRoute} from 'vue-router'
import {useTaskQuery} from '../../composables/useTasks'

const route = useRoute()
const {data, isLoading, error} = useTaskQuery(() => route.params.id)
</script>

<template>
  <p v-if="isLoading">
    Loading...
  </p>
  <p v-else-if="error">
    Error: {{ error.message }}
  </p>
  <div v-else-if="data">
    <UContainer>
      <FetchCard extended v-bind="data"/>
    </UContainer>
    <USeparator class="py-5"/>
    <UContainer>
      <h2 class="text-4xl font-bold pb-2">Fetch Log</h2>
      <FetchEventLog v-bind="data"/>
    </UContainer>
  </div>

</template>
