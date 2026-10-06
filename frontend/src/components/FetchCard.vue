<script lang="ts" setup>
import {format, parseJSON} from "date-fns";
import {computed, ref} from "vue";
import {Task} from "../api/tasks.ts";
import {utc} from "@date-fns/utc";
import {floor} from "lib0/math";
import ForceConfirmModal from "./ForceConfirmModal.vue";
import {getSafeUrl} from "../utils/url.ts";
import {useAbortTaskMutation, useRetryTaskMutation} from "../composables/useTasks.ts";

const props = defineProps<{
  task: Task,
  extended?: boolean,
  fullWidth?: boolean,
}>()

let highlightColor = computed(() => {
  switch (props.task.status) {
    case 'failed':
      return 'error'
    case 'aborting':
    case 'aborted':
      return 'warning'
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

const tsCreatedUTC = computed(() => format(parseJSON(props.task.ts_created), 'yyyy-MM-dd HH:mm', {in: utc}))

const toast = useToast()
const {mutate: abort, isPending: isAborting, error: abortError} = useAbortTaskMutation()

const {mutate: retry, isPending: isRetrying, error: retryError} = useRetryTaskMutation()

const confirmOpen = ref(false)

// the detail page (extended) aborts immediately; the list view asks first
function onAbortClick() {
  if (props.extended) {
    onAbort()
  } else {
    confirmOpen.value = true
  }
}

function onAbort() {
  confirmOpen.value = false
  abort(props.task.id, {
    onError: (err) => toast.add({
      title: 'Failed to abort fetch ' + props.task.id.slice(-4),
      description: err.message,
      icon: 'pepicons-pop:exclamation-circle-filled',
      color: 'error',
    }),
  })
}

// aborted fetches may be in an unknown state, so retrying them must bypass the sanity checks
const retryForced = computed(() => props.task.status === 'aborted')

const retryConfirmOpen = ref(false)

// forced retries skip the sanity checks, so ask first
function onRetryClick() {
  if (retryForced.value) {
    retryConfirmOpen.value = true
  } else {
    onRetry()
  }
}

function onRetry() {
  retry({id: props.task.id, force: retryForced.value}, {
    onError: (err) => toast.add({
      title: 'Failed to retry fetch ' + props.task.id.slice(-4),
      description: err.message,
      icon: 'pepicons-pop:exclamation-circle-filled',
      color: 'error',
    }),
  })
}

// retrying a successful fetch is rarely wanted, so only offer it on the detail page (extended)
const canRetry = computed(() =>
  ['failed', 'aborted'].includes(props.task.status) || (props.extended && props.task.status === 'success')
)

const canAbort = computed(() => ['created', 'running'].includes(props.task.status))

const safeAuthorUrl = computed(() => getSafeUrl(props.task.meta.author_url))

</script>
<template>
  <UChip
    :color="highlightColor"
    :text="task.status"
    :ui="{base: 'p-2 pl-3 ring-0 rounded-t-none rounded-r-none', root: fullWidth? 'flex w-full' : ''}"
    inset
    size="3xl"
  >
    <UPageCard
      :highlight-color="highlightColor"
      class="w-full"
      highlight
    >
      <template #title>
        <div class="space-x-1 flex items-center">
          <UBadge
            class="text-1xl font-mono"
            color="neutral"
          >
            <UIcon
              class="text-green-600"
              name="material-symbols:snail"
            />
            <span
              class="font-bold"
            >
              {{ taskSlugLeading }}
            </span>
            <UBadge
              v-if="taskSlugTrailing"
              class="text-sm"
              color="neutral"
              variant="soft"
            >
              <span>
                {{ taskSlugTrailing }}
              </span>
            </UBadge>
          </UBadge>
        </div>
      </template>
      <template #description>
        <span
          v-if="task.meta.name"
          class="flex items-center gap-x-1"
        >
          <UIcon name="material-symbols:article-person" />
          {{ task.meta.name }}
        </span>
        <span
          v-if="extended && task.meta.author"
          class="flex items-center gap-x-1"
        >
          <UIcon name="material-symbols:article-person" />
          <a
            v-if="safeAuthorUrl"
            :href="safeAuthorUrl"
            rel="noopener noreferrer"
          >{{ task.meta.author }}</a>
          <template v-else>{{ task.meta.author }}</template>
        </span>
        <span class="flex items-center gap-x-1 wrap-anywhere">
          <UIcon
            class="text-orange-600"
            name="material-symbols:media-link"
          />
          {{ task.url }}
        </span>
        <UBadge
          v-if="task.meta.duration && extended"
          color="neutral"
          variant="outline"
        >
          <UIcon name="material-symbols:timer-play" />
          <template v-if="task.meta.duration > 3600">
            {{ floor(task.meta.duration / 3600) }}h {{ floor((task.meta.duration % 3600) / 60) }}m
          </template>
          <template v-else-if="task.meta.duration > 60">
            {{ floor(task.meta.duration / 60) }}:{{ floor(task.meta.duration % 60) }}
          </template>
          <template v-else>
            {{ task.meta.duration }} seconds
          </template>
        </UBadge>
      </template>
      <template #footer>
        <div class="flex flex-wrap items-center justify-between gap-1">
          <div class="space-x-1 flex items-center">
            <UTooltip
              :delay-duration="0"
              text="Fetch Requested time"
            >
              <UBadge
                v-if="task.ts_created"
                class="font-mono"
                color="neutral"
                variant="outline"
              >
                <UIcon name="pepicons-pop:clock" />
                {{ tsCreatedUTC }} UTC
              </UBadge>
            </UTooltip>
            <UTooltip
              :delay-duration="0"
              text="Slurp Job ID"
            >
              <UBadge
                color="neutral"
                variant="outline"
                class="font-mono"
              >
                <UIcon name="pepicons-pop:soft-drink-circle" />
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
              v-if="task.purged"
              class="align-self-center"
              color="error"
              variant="outline"
            >
              <UIcon name="material-symbols:skull" />
              Logs Expired
            </UBadge>
            <UBadge
              v-else-if="task.pruned"
              class="align-self-center"
              color="warning"
              variant="outline"
            >
              <UIcon name="material-symbols:auto-delete" />
              Data Removed
            </UBadge>
          </div>
          <div class="ml-auto space-x-1 flex items-center">
            <UTooltip
              v-if="canAbort"
              :delay-duration="0"
              text="Abort this Fetch"
            >
              <UButton
                :color="abortError ? 'error' : 'warning'"
                :disabled="!canAbort"
                :loading="isAborting"
                icon="material-symbols:cancel"
                size="xs"
                variant="soft"
                @click.prevent.stop="onAbortClick"
              >
                Abort
              </UButton>
            </UTooltip>
            <UTooltip
              v-if="canRetry"
              :delay-duration="0"
              :text="retryForced ? 'Retry this Fetch (forced)' : 'Retry this Fetch'"
            >
              <UButton
                :color="retryError ? 'error' : 'info'"
                :disabled="!canRetry"
                :loading="isRetrying"
                icon="material-symbols:replay"
                size="xs"
                variant="soft"
                @click.prevent.stop="onRetryClick"
              >
                <b v-if="retryForced">Force Retry</b>
                <b v-else>Retry</b>
              </UButton>
            </UTooltip>
            <ForceConfirmModal
              v-model:open="retryConfirmOpen"
              @confirm="onRetry"
            />
            <UModal
              v-model:open="confirmOpen"
              :description="`This will attempt to abort fetch ${task.id.slice(-4)} (${task.url}), and may leave the fetch in an invalid state.`"
              title="Abort this Fetch?"
            >
              <template #footer>
                <div class="flex w-full justify-end gap-2">
                  <UButton
                    color="neutral"
                    variant="outline"
                    @click="confirmOpen = false"
                  >
                    Cancel
                  </UButton>
                  <UButton
                    color="warning"
                    icon="material-symbols:cancel"
                    @click="onAbort"
                  >
                    Request Abort
                  </UButton>
                </div>
              </template>
            </UModal>
          </div>
        </div>
      </template>
    </UPageCard>
  </UChip>
</template>
