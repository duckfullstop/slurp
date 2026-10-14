export interface FetchUpdatedEvent {
  fetch_id: string
  state: 'success' | 'failed' | 'aborted' | 'aborted-playlist'
  path?: string
  message?: string
}
