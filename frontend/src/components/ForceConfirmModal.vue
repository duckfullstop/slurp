<script lang="ts" setup>
defineProps<{
  // Describes what is about to be forced, shown beneath the title
  description?: string | null,
}>()

const WARNING = 'This will skip the sanity checks that normally stop a fetch from proceeding.'

const open = defineModel<boolean>('open', {default: false})

const emit = defineEmits<{
  confirm: []
}>()

function onConfirm() {
  open.value = false
  emit('confirm')
}
</script>
<template>
  <UModal
    v-model:open="open"
    :description="description ? `${description} ${WARNING}` : WARNING"
    title="Skip checks?"
  >
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton
          color="neutral"
          variant="outline"
          @click="open = false"
        >
          Cancel
        </UButton>
        <UButton
          color="warning"
          icon="material-symbols:replay"
          @click="onConfirm"
        >
          Skip Checks and Fetch
        </UButton>
      </div>
    </template>
  </UModal>
</template>
