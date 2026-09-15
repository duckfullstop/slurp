/// <reference types="vite/client" />
interface ViteTypeOptions {
  // Disallow unknown keys.
  strictImportMetaEnv: unknown
}

interface ImportMetaEnv {
  readonly VITE_APP_NAME: string
  readonly VITE_APP_ICON: string
  readonly VITE_APP_COPYRIGHT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare const __APP_COMMIT__: string
declare const __APP_VERSION__: string
