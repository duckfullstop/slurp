export interface FetchUpdatedEvent {
  fetch_id: string
  state: 'success' | 'failed' | 'aborted'
  path?: string
  message?: string
}
