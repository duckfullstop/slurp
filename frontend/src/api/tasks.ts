export interface FetchMetadata {
  name?: string
  author?: string
  author_url?: string
  ts_upload?: string
  duration?: number
  format?: string
  thumbnail_url?: string
}

export interface Task {
  id: string
  ts_created: string
  ts_updated: string
  url: string
  slug: string
  format: string
  target: string
  status: string
  meta: FetchMetadata
  output_path?: string
  pruned: boolean
  purged: boolean
  worker_id?: string
}

export interface FetchEvent {
  ts_created: string
  fetch_id: string
  typ: string
  level: string
  message: string
  status: string
}

export async function fetchTasks(): Promise<Task[]> {
  const res = await fetch('/api/v1/task/')
  if (!res.ok) {
    throw new Error(`Failed to fetch tasks: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<Task[]>
}

export async function fetchTask(id: string): Promise<Task> {
  const res = await fetch(`/api/v1/task/${id}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch task ${id}: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<Task>
}

export async function fetchTaskEvents(id: string): Promise<FetchEvent[]> {
  const res = await fetch(`/api/v1/task/${id}/events`)
  if (!res.ok) {
    throw new Error(`Failed to fetch task ${id} events: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<FetchEvent[]>
}

