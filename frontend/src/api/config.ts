export interface AppConfigFetcher {
  services: string[]
}

export interface AppConfig {
  outputs: {
    [key: string]: string
  }
  fetchers: {
    [key: string]: AppConfigFetcher
  }
  purge: number
  prune: number
}

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch('/api/v1/config/')
  if (!res.ok) {
    throw new Error(`Failed to fetch app configuration: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<AppConfig>
}
