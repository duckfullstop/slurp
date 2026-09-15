<script lang="ts" setup>
import {reactive, watch} from 'vue'
import type {FormSubmitEvent} from '@nuxt/ui'
import {useConfigQuery, useCreateTaskMutation} from '../composables/useTasks'
import {type CreateTaskInput, createTaskSchema, FORMAT_OPTIONS} from '../schemas/createTask'

const toast = useToast()

const {data: config, isLoading: isLoadingConfig, error: configError} = useConfigQuery()
const mutation = useCreateTaskMutation()

const state = reactive<Partial<CreateTaskInput>>({
  url: undefined,
  slug: undefined,
  format: 'VIDEO_AUDIO',
  target: undefined
})

watch(config, (newConfig) => {
  if (!state.target && newConfig?.outputs?.length) {
    state.target = newConfig.outputs[0]
  }
}, {immediate: true})

async function onSubmit(event: FormSubmitEvent<CreateTaskInput>) {
  try {
    await mutation.mutateAsync(event.data)
    console.log(event.data)
    toast.add({
      title: 'Ingest task created successfully.',
      icon: 'pepicons-pop:soft-drink-circle-off'
    })
    // Reset state
    state.url = undefined
    state.slug = undefined
    state.format = 'VIDEO_AUDIO'
    state.target = config.value?.outputs?.[0]
  } catch (error: unknown) {
    console.error(error)
    toast.add({
      title: 'Oh no! Problem with request',
      description: error instanceof Error ? error.message : String(error),
      icon: 'pepicons-pop:soft-drink-circle-off'
    })
  }
}


</script>

<template>
  <UForm :schema="createTaskSchema" :state="state" class="space-y-4" @submit="onSubmit">
    <UFormField label="🌐 URL" name="url" required>
      <UInput v-model="state.url" class="w-full" placeholder="URL"/>
    </UFormField>

    <UFormField label="🐌 Slug" name="slug" required>
      <UInput v-model="state.slug" class="w-full" placeholder="Slug"/>
    </UFormField>

    <UFormField label="✍️ Format" name="format" required>
      <USelect v-model="state.format" :items="FORMAT_OPTIONS"
               class="w-full" placeholder="Select an output format"/>
    </UFormField>

    <UFormField :error="configError ? configError.message : undefined" label="📁 Target" name="target" required>
      <USelect
        v-model="state.target"
        :disabled="isLoadingConfig || !!configError"
        :items="config?.outputs ?? []"
        :loading="isLoadingConfig"
        class="w-full"
        placeholder="Select a target output directory"
      />
    </UFormField>

    <UAlert
      v-if="mutation.isSuccess.value"
      :description="`Task ${mutation.data.value?.fetch_id} was created.`"
      color="success"
      title="Fetch successfully requested."
    />
    <UAlert
      v-if="mutation.isError.value"
      :description="mutation.error.value?.message"
      color="error"
      title="Issue requesting slurp"
    />

    <UButton :disabled="isLoadingConfig || !!configError" :loading="mutation.isPending.value" color="info"
             type="submit">
      <UIcon name="pepicons-pop:soft-drink"/>
      Slurp Media
    </UButton>
  </UForm>
</template>
