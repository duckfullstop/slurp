<script lang="ts" setup>

import {computed, ref, useTemplateRef, watch} from "vue";
import {useScroll} from "@vueuse/core";
import {useQueryClient} from "@tanstack/vue-query";
import {useTaskEventsQuery} from "../composables/useTasks.ts";
import {useLiveEvents} from "../composables/useLiveEvents";
import type {FetchEvent} from "../api/tasks";
import FetchEventLogEntry from "./FetchEventLogEntry.vue";

const props = defineProps<{
  id: string
}>()

const {data, isLoading, error} = useTaskEventsQuery(() => props.id)

const queryClient = useQueryClient()
const {data: liveData, event: liveEvent} = useLiveEvents()

watch([liveData, liveEvent], ([raw, type]) => {
  if (!raw || type !== null) return
  const logEvent = JSON.parse(raw) as FetchEvent
  if (logEvent.fetch_id !== props.id) return
  queryClient.setQueryData<FetchEvent[]>(['taskEvents', props.id], (old) => [...(old ?? []), logEvent])
})

const scrollAreaRef = useTemplateRef("scrollAreaRef")
const scrollEl = computed(() => scrollAreaRef.value?.$el)
const {y, arrivedState} = useScroll(scrollEl, {offset: {bottom: 4}})

const stickToBottom = ref(true)
watch(() => arrivedState.bottom, (atBottom) => {
  stickToBottom.value = atBottom
})

watch(() => props.id, () => {
  stickToBottom.value = true
})

function scrollToBottom() {
  const el = scrollEl.value
  if (el) y.value = el.scrollHeight
}

watch(() => data.value?.length, () => {
  if (stickToBottom.value) scrollToBottom()
}, {flush: "post"})

function jumpToLive() {
  stickToBottom.value = true
  scrollToBottom()
}
</script>
<template>
  <p v-if="isLoading">
    <USkeleton class="h-96 w-full"/>
  </p>
  <p v-else-if="error">
    <UAlert
      :description="error.message"
      color="error"
      icon="pepicons-pop:exclamation-circle-filled"
      title="Error loading Fetch Events"
      variant="solid"
    />
  </p>
  <div v-else-if="data" class="relative">
    <UScrollArea ref="scrollAreaRef" v-slot="{ item }" :items="data"
                 class="w-full h-96 bg-black dark:bg-black">
      <FetchEventLogEntry :event="item"/>
      <USeparator></USeparator>
    </UScrollArea>
    <UBadge v-if="stickToBottom" class="absolute bottom-0 right-4 z-10 items-center gap-1.5 rounded-b-none"
            color="success"
            variant="subtle">
      <span class="size-2 rounded-full bg-success-500 animate-pulse"/>
      Live
    </UBadge>
    <UButton v-else class="absolute bottom-0 right-4 z-10 rounded-b-none" color="neutral" size="xs" variant="subtle"
             @click="jumpToLive">
      Paused — jump to latest
    </UButton>
  </div>
</template>
