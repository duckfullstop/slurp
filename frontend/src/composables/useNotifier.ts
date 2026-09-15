import {watch} from 'vue'
import {useToast} from '@nuxt/ui/composables'
import {useLiveEvents} from './useLiveEvents'
import {FetchUpdatedEvent} from "../api/events.ts";
import {usePermission, useWebNotification} from "@vueuse/core";

export function useNotifier() {
  const toast = useToast()
  const {data, event} = useLiveEvents()

  const notifyPermission = usePermission('notifications')

  watch([data, event], ([raw, type]) => {
    if (type !== 'fetch_updated' || !raw) return
    const update = JSON.parse(raw) as FetchUpdatedEvent
    let title: string
    let body: string | undefined
    let icon: string
    let color: 'success' | 'error'

    if (update.state === 'success') {
      title = 'Fetch ' + update.fetch_id.slice(-4) + ' succeeded'
      body = ''
      icon = 'pepicons-pop:checkmark-circle-filled'
      color = 'success'
    } else {
      title = 'Fetch ' + update.fetch_id.slice(-4) + ' failed'
      body = update.message
      icon = 'pepicons-pop:exclamation-circle-filled'
      color = 'error'
    }
    toast.add({
      title: title,
      description: body,
      icon: icon,
      color: color
    })
    const {
      isSupported,
      permissionGranted,
      show,
    } = useWebNotification({
      title: 'Hello, VueUse world!',
      dir: 'auto',
      lang: 'en',
      renotify: true,
      tag: 'test',
    })

    if (notifyPermission.value && isSupported.value && permissionGranted.value) {
      show()
    }

  })
}
