export interface FetchUpdatedEvent {
  fetch_id: string
  state: 'success' | 'failed'
  path?: string
  message?: string
}
