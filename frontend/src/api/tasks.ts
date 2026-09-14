import type {CreateTaskInput} from '../schemas/createTask'

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
  status: number
}

export interface AppConfig {
  outputs: string[]
}

export interface CreateTaskResponse {
  fetch_id: string
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

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch('/api/v1/config/')
  if (!res.ok) {
    throw new Error(`Failed to fetch app configuration: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<AppConfig>
}

export async function createTask(payload: CreateTaskInput): Promise<CreateTaskResponse> {
  const res = await fetch('/api/v1/task/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    throw new Error(`Failed to create task: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<CreateTaskResponse>
}

