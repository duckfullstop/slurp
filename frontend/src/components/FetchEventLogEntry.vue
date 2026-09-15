<script lang="ts" setup>
import {FetchEvent} from "../api/tasks.ts";
import {computed} from "vue";
import {format} from "date-fns";

const props = defineProps<{
  event: FetchEvent
}>()

let highlightColor = computed(() => {
  switch (props.event.level) {
    case 'error':
      return 'text-error-500'
    case 'success':
      return 'text-success-500'
    case 'info':
      return ''
    case 'warning':
      return 'text-warning-500'
    case 'debug':
      return 'text-muted-500'
    default:
      return ''
  }
})
</script>

<template>
  <UCard
    :ui="{
      body: 'sm:py-1 sm:px-1 py-1 px-1'
    }"
    class="font-mono ring-0 dark:bg-gray-900 dark:text-white"
    variant="solid"
  >
    <div class="flex flex-row flex-wrap space-x-5">
      <div class="flex-none sm:basis-full md:basis-auto">
        {{ format(event.ts_created, 'yyyy-MM-dd HH:MM') }} UTC
      </div>
      <!-- TODO this doesn't wrap right on smaller displays. -->
      <div
        :class="highlightColor"
        class="flex-none md:flex-1"
      >
        {{ event.message }}
      </div>
    </div>
  </UCard>
</template>
