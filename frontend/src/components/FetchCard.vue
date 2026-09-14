<script lang="ts" setup>
import {format} from "date-fns";
import {computed} from "vue";

const props = defineProps<{
  id: string
  status?: string
  slug?: string
  url?: string
  ts_created?: string
}>()

let highlightColor = computed(() => {
  switch (props.status) {
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
  <RouterLink :to="{name: '/fetch/[id]', params: {id: props.id}}">
    <UPageCard :highlight-color="highlightColor" highlight>
      <template #title>
        <div class="space-x-1 flex items-center">
          <UBadge class="text-1xl" color="neutral">
            <UIcon name="material-symbols:snail"/>
            {{ props.slug }}
          </UBadge>
          <UBadge :color="highlightColor" class="text-1xl">{{ props.status }}</UBadge>
        </div>
      </template>
      <template #description>
        <span>{{ props.url }}</span>
      </template>
      <template #footer>
        <div class="space-x-1 flex items-center justify-center">
          <UPopover enable-touch mode="hover">
            <UBadge color="neutral" variant="outline">
              <UIcon name="pepicons-pop:soft-drink-circle"/>
              {{ props.id.slice(-4) }}
            </UBadge>

            <template #content>
              <div class="p-1">Slurp Job ID</div>
            </template>
          </UPopover>
          <UBadge v-if="props.ts_created" color="neutral" variant="outline">
            <UIcon name="pepicons-pop:clock"/>
            {{ format(props.ts_created, 'yyyy-MM-dd HH:MM') }} UTC
          </UBadge>
        </div>
      </template>
    </UPageCard>
  </RouterLink>
</template>
