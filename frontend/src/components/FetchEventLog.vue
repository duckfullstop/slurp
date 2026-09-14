<script lang="ts" setup>

import {useTaskEventsQuery} from "../composables/useTasks.ts";
import FetchEventLogEntry from "./FetchEventLogEntry.vue";

const props = defineProps<{
  id: string
}>()

const {data, isLoading, error} = useTaskEventsQuery(() => props.id)
</script>
<template>
  <p v-if="isLoading">
    Loading...
  </p>
  <p v-else-if="error">
    Error: {{ error.message }}
  </p>
  <UScrollArea v-else-if="data" v-slot="{ item }" :items="data"
               class="w-full h-96 bg-black dark:bg-black">
    <FetchEventLogEntry :event="item"/>
    <USeparator></USeparator>
  </UScrollArea>
</template>
