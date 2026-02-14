/**
 * useTheme - Theme management hook with Light/Dark/System support.
 *
 * Uses useSyncExternalStore for React 18+ compatible reactivity.
 * Reads from localStorage, falls back to system preference.
 * When 'system', listens to matchMedia changes.
 * Adds/removes 'dark' class on document.documentElement.
 */

import { useSyncExternalStore, useCallback } from 'react'

export type Theme = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'launch-theme'

// ---------------------------------------------------------------------------
// Internal store shared across all hook instances
// ---------------------------------------------------------------------------

let listeners: Array<() => void> = []

function emitChange() {
  for (const listener of listeners) {
    listener()
  }
}

function subscribe(listener: () => void) {
  listeners = [...listeners, listener]
  return () => {
    listeners = listeners.filter((l) => l !== listener)
  }
}

function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'system'
  return (localStorage.getItem(STORAGE_KEY) as Theme) || 'system'
}

function getSystemPreference(): ResolvedTheme {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function resolveTheme(theme: Theme): ResolvedTheme {
  if (theme === 'system') return getSystemPreference()
  return theme
}

function applyTheme(resolved: ResolvedTheme) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  if (resolved === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

// Snapshot function for useSyncExternalStore
function getSnapshot(): Theme {
  return getStoredTheme()
}

function getServerSnapshot(): Theme {
  return 'system'
}

// ---------------------------------------------------------------------------
// Listen to system preference changes
// ---------------------------------------------------------------------------

if (typeof window !== 'undefined') {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', () => {
    const theme = getStoredTheme()
    if (theme === 'system') {
      applyTheme(resolveTheme('system'))
      emitChange()
    }
  })

  // Apply theme on initial load
  applyTheme(resolveTheme(getStoredTheme()))
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
  const resolvedTheme = resolveTheme(theme)

  const setTheme = useCallback((newTheme: Theme) => {
    if (typeof window === 'undefined') return
    localStorage.setItem(STORAGE_KEY, newTheme)
    applyTheme(resolveTheme(newTheme))
    emitChange()
  }, [])

  return { theme, setTheme, resolvedTheme } as const
}
