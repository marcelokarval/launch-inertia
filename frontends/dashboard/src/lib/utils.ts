/**
 * Utility functions - HeroUI v3 Native
 *
 * NÃO usa cn() do Shadcn/UI!
 * Para styling, use tv() de @heroui/styles
 */

/**
 * Format currency values.
 */
export function formatCurrency(
  amount: number,
  currency = 'BRL',
  locale?: string
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount / 100) // Stripe uses cents
}

/**
 * Format date values.
 */
export function formatDate(
  date: Date | string,
  options?: Intl.DateTimeFormatOptions,
  locale?: string
): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat(locale, options).format(d)
}

/**
 * Format relative time (e.g., "2 hours ago").
 */
export function formatRelativeTime(date: Date | string, locale?: string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diff = now.getTime() - d.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })

  if (days > 0) return rtf.format(-days, 'day')
  if (hours > 0) return rtf.format(-hours, 'hour')
  if (minutes > 0) return rtf.format(-minutes, 'minute')
  return rtf.format(-seconds, 'second')
}

/**
 * Check if code is running on client side.
 */
export function isClient(): boolean {
  return typeof window !== 'undefined'
}

/**
 * Debounce function for rate limiting.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Generate unique ID.
 */
export function generateId(prefix = 'id'): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
}
