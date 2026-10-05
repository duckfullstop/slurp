<script lang="ts" setup>
import {computed, reactive, watch} from 'vue'
import type {FormSubmitEvent, SelectItem} from '@nuxt/ui'
import {useCreateTaskMutation} from '../composables/useTasks'
import {type CreateTaskBatchInput, createTaskBatchSchema, FORMAT_OPTIONS, parseUrlList} from '../schemas/createTask'
import {useConfigQuery} from "../composables/useConfig.ts";

const toast = useToast()

const {data: config, isLoading: isLoadingConfig, error: configError} = useConfigQuery()
const mutation = useCreateTaskMutation()

const state = reactive<Partial<CreateTaskBatchInput>>({
  urls: undefined,
  slug: undefined,
  format: 'VIDEO_AUDIO',
  target: undefined
})

const urlCount = computed(() => parseUrlList(state.urls).length)

const slugExample = computed(() => `${state.slug?.trim() || 'TST000 Example Slug'} - 01`)

const targetOptions =computed<SelectItem[]>(() =>
  Object.entries(config.value?.outputs ?? {}).map(([value, label]) => ({value, label}))
)

watch(config, (newConfig) => {
  if (!state.target && newConfig?.outputs) {
    const [firstTarget] = Object.keys(newConfig.outputs)
    if (firstTarget) state.target = firstTarget
  }
}, {immediate: true})

async function onSubmit(event: FormSubmitEvent<CreateTaskBatchInput>) {
  const {urls, ...common} = event.data
  const results = await Promise.allSettled(
    parseUrlList(urls).map((url, index) => mutation.mutateAsync({
      ...common,
      url,
      slug: `${common.slug} - ${String(index + 1).padStart(2, '0')}`
    }))
  )

  const failed = results.flatMap((result, index) =>
    result.status === 'rejected' ? [{index, reason: result.reason}] : []
  )
  const succeeded = results.length - failed.length

  if (succeeded > 0) {
    toast.add({
      title: `${succeeded} ingest task${succeeded === 1 ? '' : 's'} created successfully.`,
      icon: 'pepicons-pop:soft-drink-circle'
    })
  }

  if (failed.length > 0) {
    const submitted = parseUrlList(urls)
    console.error(failed)
    toast.add({
      title: `${failed.length} of ${results.length} requests failed`,
      description: failed
        .map(({index, reason}) => `${submitted[index]}: ${reason instanceof Error ? reason.message : String(reason)}`)
        .join('\n'),
      icon: 'pepicons-pop:soft-drink-circle-off'
    })
    // Keep only the failed URLs so the user can retry them.
    state.urls = failed.map(({index}) => submitted[index]).join('\n')
    return
  }

  // Reset state
  state.urls = undefined
  state.slug = undefined
  state.format = 'VIDEO_AUDIO'
  state.target = Object.keys(config.value?.outputs ?? {})[0]
}
</script>

<template>
  <UForm
    :schema="createTaskBatchSchema"
    :state="state"
    class="space-y-4"
    @submit="onSubmit"
  >
    <UAlert
      color="info"
      description="There is no handling or checking for file name collisions. Not heeding this warning may result in files being overwritten, or other unexpected behaviour. If you need to ingest further files over the top of an already completed workflow, please slurp each one individually in Single mode."
      icon="material-symbols:warning"
      title="Don't multi-slurp the same slug twice!"
    />
    <div class="flex flex-wrap gap-x-5 md:gap-x-10">
      <UFormField
        :help="`${urlCount} URL${urlCount === 1 ? '' : 's'} (one per line)`"
        :ui="{label: 'flex items-center gap-x-1'}"
        class="flex-grow-1"
        label="🌐 URLs"
        name="urls"
        required
        size="xl"
      >
        <template #label>
          <UIcon
            class="text-orange-600"
            name="material-symbols:media-link"
          /> URLs
        </template>
        <UTextarea
          v-model="state.urls"
          :rows="6"
          autoresize
          class="w-full font-mono"
          placeholder="https://www.youtube.com/watch?v=...&#10;https://www.youtube.com/watch?v=..."
        />
      </UFormField>
    </div>


    <UFormField
      :ui="{label: 'flex items-center gap-x-1 font-sans'}"
      label="🐌 Slug"
      name="slug"
      required
      size="xl"
    >
      <template #help>
        Each URL will get a numbered slug, e.g. <span class="font-mono">{{ slugExample }}</span>
      </template>
      <template #label>
        <UIcon
          class="text-green-600"
          name="material-symbols:snail"
        /> Slug
      </template>
      <UInput
        v-model="state.slug"
        class="w-full"
        placeholder="TST000 Example Slug"
      />
    </UFormField>

    <div class="flex flex-wrap  gap-x-5 md:gap-x-10">
      <UFormField
        :ui="{label: 'flex items-center gap-x-1'}"
        class="flex-grow-1"
        label="✍️ Format"
        name="format"
        required
        size="xl"
      >
        <template #label>
          <UIcon name="material-symbols:convert-to-text" /> Format
        </template>
        <USelect
          v-model="state.format"
          :items="FORMAT_OPTIONS"
          class="w-full"
          placeholder="Select an output format"
        />
      </UFormField>

      <UFormField
        :error="configError ? configError.message : undefined"
        :ui="{label: 'flex items-center gap-x-1'}"
        class="flex-grow-1"
        label="📁 Target"
        name="target"
        required
        size="xl"
      >
        <template #label>
          <UIcon name="material-symbols:file-open" /> Target
        </template>
        <USelect
          v-model="state.target"
          :disabled="isLoadingConfig || !!configError"
          :items="targetOptions"
          :loading="isLoadingConfig"
          class="w-full"
          placeholder="Select a target output directory"
        />
      </UFormField>
    </div>

    <UButton
      :disabled="isLoadingConfig || !!configError"
      :loading="mutation.isPending.value"
      color="info"
      type="submit"
    >
      <UIcon name="pepicons-pop:soft-drink" />
      Slurp {{ urlCount > 1 ? `${urlCount} Items` : 'Media' }}
    </UButton>
  </UForm>
</template>
