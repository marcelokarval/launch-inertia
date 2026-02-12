/**
 * ThemeToggle - Cycles through light / dark / system on each click.
 *
 * Uses useTheme hook.
 */

import { Sun, Moon, Monitor } from 'lucide-react'
import { Button as HeroButton } from '@heroui/react'
import { useTheme, type Theme } from '@/hooks/useTheme'
import { useTranslation } from 'react-i18next'

const CYCLE: Theme[] = ['light', 'dark', 'system']

const icons: Record<Theme, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
}

const labelKeys: Record<Theme, string> = {
  light: 'themeToggle.light',
  dark: 'themeToggle.dark',
  system: 'themeToggle.system',
}

export interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme()
  const { t } = useTranslation('components')

  function handleClick() {
    const currentIndex = CYCLE.indexOf(theme)
    const nextIndex = (currentIndex + 1) % CYCLE.length
    setTheme(CYCLE[nextIndex])
  }

  const Icon = icons[theme]
  const label = t(labelKeys[theme])

  return (
    <HeroButton
      variant="ghost"
      size="sm"
      isIconOnly
      onPress={handleClick}
      className={`text-default-500 hover:text-default-700 ${className}`}
      aria-label={label}
    >
      <Icon className="h-5 w-5" />
    </HeroButton>
  )
}
