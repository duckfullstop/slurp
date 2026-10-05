import {watch} from 'vue'
import {useToast} from '@nuxt/ui/composables'
import {useLiveEvents} from './useLiveEvents'
import {FetchUpdatedEvent} from "../api/events.ts";
import {usePermission, useStorage, useWebNotification} from "@vueuse/core";
import {useSound} from "@vueuse/sound";

const SUCCESS_SOUNDS = ['/sound/success1.mp3', '/sound/success2.mp3']
const FAILURE_SOUNDS = ['/sound/failure1.mp3']

export function useNotifier() {
  const toast = useToast()
  const {data, event} = useLiveEvents()

  const notifyPermission = usePermission('notifications')

  const soundEnabled = useStorage('slurp:sound-enabled', false)

  const successSounds = SUCCESS_SOUNDS.map(url => useSound(url))
  const failureSounds = FAILURE_SOUNDS.map(url => useSound(url))
  const playRandom = (sounds: ReturnType<typeof useSound>[]) =>
    sounds[Math.floor(Math.random() * sounds.length)]?.play()

  const {
    isSupported,
    permissionGranted,
    show,
  } = useWebNotification({
    lang: 'en',
    renotify: true,
    silent: true, // we play our own sound
    tag: 'slurp',
  })

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
    } else if (update.state === 'aborted') {
      title = 'Fetch ' + update.fetch_id.slice(-4) + ' aborted'
      body = update.message
      icon = 'pepicons-pop:exclamation-circle-filled'
      color = 'error'
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

    if (soundEnabled.value) playRandom(color === 'success' ? successSounds : failureSounds)

    if (notifyPermission.value && isSupported.value && permissionGranted.value) {
      show({
        title: title,
        body: body
      })
    }

  })

  return {soundEnabled}
}
