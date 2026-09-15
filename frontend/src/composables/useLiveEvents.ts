import {createSharedComposable, useEventSource} from '@vueuse/core'

/**
 * Shared live event stream for Slurp's Fetch tasks, published by the backend over SSE.
 * `event` is `null` for a plain Fetch log line, or one of "task_created" / "metadata" / "fetch_updated".
 */
export const useLiveEvents = createSharedComposable(() => useEventSource(
  '/api/v1/stream',
  ['task_created', 'metadata', 'fetch_updated'],
  {
    autoReconnect: {
      delay: 1000,
    }
  }
))
