<script lang="ts" setup>
import {computed, reactive, ref, watch} from 'vue'
import type {Form, FormSubmitEvent, SelectItem} from '@nuxt/ui'
import {useCreateTaskMutation} from '../composables/useTasks'
import {type CreateTaskInput, createTaskSchema, FORMAT_OPTIONS} from '../schemas/createTask'
import {useRouter} from "vue-router";
import {useConfigQuery} from "../composables/useConfig.ts";

const toast = useToast()

const router = useRouter()

const {data: config, isLoading: isLoadingConfig, error: configError} = useConfigQuery()
const mutation = useCreateTaskMutation()

const form = ref<Form<CreateTaskInput> | null>(null)

// Tracks which button triggered the form submission
type SubmitAction = 'redirect' | 'background'
const submitAction = ref<SubmitAction>('redirect')

const state = reactive<Partial<CreateTaskInput>>({
  url: undefined,
  slug: undefined,
  format: 'VIDEO_AUDIO',
  target: undefined
})

const targetOptions = computed<SelectItem[]>(() =>
  Object.entries(config.value?.outputs ?? {}).map(([value, label]) => ({value, label}))
)

watch(config, (newConfig) => {
  if (!state.target && newConfig?.outputs) {
    const [firstTarget] = Object.keys(newConfig.outputs)
    if (firstTarget) state.target = firstTarget
  }
}, {immediate: true})

async function onSubmit(event: FormSubmitEvent<CreateTaskInput>) {
  // Reset the submitAction state, otherwise the redirect button doesn't do what you expect on subsequent clicks.
  const action = submitAction.value
  submitAction.value = 'redirect'
  try {
    const response = await mutation.mutateAsync(event.data)
    toast.add({
      title: 'Ingest task created successfully.',
      icon: 'pepicons-pop:soft-drink-circle'
    })
    // Reset state
    state.url = undefined
    state.slug = undefined
    state.format = 'VIDEO_AUDIO'
    state.target = Object.keys(config.value?.outputs ?? {})[0]

    if (action === 'redirect') {
      router.push({name: '/fetch/[id]', params: {id: response.fetch_id}})
    }
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
  <UForm
    ref="form"
    :schema="createTaskSchema"
    :state="state"
    class="space-y-4"
    @submit="onSubmit"
  >
    <UFormField
      label="🌐 URL"
      name="url"
      required
    >
      <UInput
        v-model="state.url"
        class="w-full"
        placeholder="URL"
      />
    </UFormField>

    <UFormField
      label="🐌 Slug"
      name="slug"
      required
    >
      <UInput
        v-model="state.slug"
        class="w-full"
        placeholder="Slug"
      />
    </UFormField>

    <UFormField
      label="✍️ Format"
      name="format"
      required
    >
      <USelect
        v-model="state.format"
        :items="FORMAT_OPTIONS"
        class="w-full"
        placeholder="Select an output format"
      />
    </UFormField>

    <UFormField
      :error="configError ? configError.message : undefined"
      label="📁 Target"
      name="target"
      required
    >
      <USelect
        v-model="state.target"
        :disabled="isLoadingConfig || !!configError"
        :items="targetOptions"
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


    <UFieldGroup
      :disabled="isLoadingConfig || !!configError"
      :loading="mutation.isPending.value"
    >
      <UButton
        color="info"
        type="submit"
        @click="submitAction = 'redirect'"
      >
        <UIcon name="pepicons-pop:soft-drink"/>
        Slurp Media
      </UButton>
      <UDropdownMenu
        :items="[
          {
            label: 'Queue in Background',
            icon: 'pepicons-pop:arrow-right',
            onSelect() {
              submitAction = 'background'
              form?.submit()
            }
          }
        ]"
      >
        <UButton
          color="info"
          icon="i-lucide-chevron-down"
          variant="soft"
        />
      </UDropdownMenu>
    </UFieldGroup>
  </UForm>
</template>
