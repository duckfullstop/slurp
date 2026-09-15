<script lang="ts" setup>
import {format} from "date-fns";
import {computed} from "vue";
import {Task} from "../api/tasks.ts";

const props = defineProps<{
  task: Task,
  extended?: boolean
}>()

let highlightColor = computed(() => {
  switch (props.task.status) {
    case 'failed':
      return 'error'
    case 'success':
      return 'success'
    case 'running':
      return 'info'
    default:
      return 'neutral'
  }
})
</script>
<template>
  <UPageCard
    :highlight-color="highlightColor"
    highlight
  >
    <template #title>
      <div class="space-x-1 flex items-center">
        <UBadge
          class="text-1xl"
          color="neutral"
        >
          <UIcon name="material-symbols:snail"/>
          {{ task.slug }}
        </UBadge>
        <UBadge
          :color="highlightColor"
          class="text-1xl"
        >
          {{ task.status }}
        </UBadge>
      </div>
    </template>
    <template #description>
      <span>{{ task.url }}</span>
    </template>
    <template #footer>
      <div class="space-x-1 flex items-center justify-center">
        <UTooltip
          :delay-duration="0"
          text="Slurp Job ID"
        >
          <UBadge
            color="neutral"
            variant="outline"
          >
            <UIcon name="pepicons-pop:soft-drink-circle"/>
            <span
              v-if="props.extended"
              class="text-muted"
            >
              {{ task.id.slice(0, -4) }}
            </span>
            <span class="font-bold">
              {{ task.id.slice(-4) }}
            </span>
          </UBadge>
        </UTooltip>
        <UBadge
          v-if="task.ts_created"
          color="neutral"
          variant="outline"
        >
          <UIcon name="pepicons-pop:clock"/>
          {{ format(task.ts_created, 'yyyy-MM-dd HH:MM') }} UTC
        </UBadge>
      </div>
    </template>
  </UPageCard>
</template>
