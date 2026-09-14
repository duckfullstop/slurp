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
    <UPageSection>
      <FetchCard v-bind="data"/>
    </UPageSection>
    <UContainer>
      <h2 class="text-4xl font-bold">Test</h2>
      <FetchEventLog v-bind="data"/>
    </UContainer>
  </div>

</template>
