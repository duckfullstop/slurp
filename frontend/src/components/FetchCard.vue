<script lang="ts" setup>
import {format, parseJSON} from "date-fns";
import {computed} from "vue";
import {Task} from "../api/tasks.ts";
import {utc} from "@date-fns/utc";

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

let taskSlugLeading = computed(() => {
  return props.task.slug.split(' ', 1)[0]
})

let taskSlugTrailing = computed(() => {
  // fun and interesting way of getting everything after the first space
  return props.task.slug.split(' ').slice(1).join(' ')
})

const tsCreatedUTC = computed(() => (format(parseJSON(props.task.ts_created), 'yyyy-MM-dd HH:mm', {in: utc})))

</script>
<template>
  <UChip
    :color="highlightColor"
    :text="task.status"
    :ui="{base: 'p-2 pl-3 ring-0 rounded-t-none rounded-r-none'}"
    inset
    size="3xl"
  >
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
            <span
              class="font-bold"
            >
              {{ taskSlugLeading }}
            </span>
          </UBadge>
          <UBadge
            v-if="taskSlugTrailing"
            class="text-1xl"
            color="neutral"
          >
            <UIcon name="material-symbols:description"/>
            <span>
              {{ taskSlugTrailing }}
            </span>
          </UBadge>
        </div>
      </template>
      <template #description>
        <p class="wrap-anywhere">
          {{ task.url }}
        </p>
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
            {{ tsCreatedUTC }} UTC
          </UBadge>
        </div>
      </template>
    </UPageCard>
  </UChip>
</template>
