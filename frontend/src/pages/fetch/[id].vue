<script lang="ts" setup>
import {useRoute} from 'vue-router'
import {useTaskQuery} from '../../composables/useTasks'

const route = useRoute<'/fetch/[id]'>()
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
      <FetchCard :id="data.id" :slug="data.slug" :status="data.status" :ts_created="data.ts_created"
                 :url="data.url" extended/>
    </UContainer>
    <USeparator class="py-5"/>
    <UContainer>
      <h2 class="text-4xl font-bold pb-2">Fetch Log</h2>
      <FetchEventLog :id="data.id"/>
    </UContainer>
  </div>

</template>
