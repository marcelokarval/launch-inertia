/**
 * Custom Hooks
 *
 * Para formularios, usa-se useForm nativo do @inertiajs/react.
 * useAppForm wraps useForm with forceFormData: true by default.
 */

// Re-export Inertia.js hooks (useForm intentionally NOT re-exported — use useAppForm instead)
export { usePage, router } from '@inertiajs/react'

// Custom hooks
export { useTheme } from './useTheme'
export type { Theme, ResolvedTheme } from './useTheme'

export { useAppForm } from './useAppForm'
