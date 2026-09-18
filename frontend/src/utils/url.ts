const SAFE_URL_SCHEMES = new Set(["http:", "https:"])

/**
 * Returns `url` unchanged if it's a valid absolute http(s) URL, otherwise `undefined`
 */
export function getSafeUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined
  try {
    return SAFE_URL_SCHEMES.has(new URL(url).protocol) ? url : undefined
  } catch {
    return undefined
  }
}
