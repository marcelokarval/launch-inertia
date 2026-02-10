import type { SharedUser } from '@/types'

export interface FlashMessages {
  success?: string | null
  error?: string | null
  warning?: string | null
  info?: string | null
}

export interface AppConfig {
  name: string
  debug: boolean
  locale: string
  timezone: string
  csrf_token: string
}

export interface SharedProps {
  auth: {
    user: SharedUser | null
  }
  flash: FlashMessages
  app: AppConfig
}

export type PageProps<T extends Record<string, unknown> = Record<string, unknown>> = T & SharedProps

declare module '@inertiajs/react' {
  export function usePage<T extends PageProps = PageProps>(): {
    props: T
    url: string
    component: string
    version: string | null
    scrollRegions: Array<{ top: number; left: number }>
    rememberedState: Record<string, unknown>
  }
}
