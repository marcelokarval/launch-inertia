/**
 * LanguageSelector - HeroUI Dropdown to switch between supported languages.
 *
 * Props:
 * - visualOnly: if true, changes language without persisting to localStorage
 *   (used on login page where the user may not be the account owner).
 * - className: optional extra classes
 */

import { Globe } from 'lucide-react'
import { Dropdown, Button as HeroButton } from '@heroui/react'
import { useTranslation } from 'react-i18next'
import {
  LANGUAGE_OPTIONS,
  getCurrentLanguage,
  persistLanguage,
  changeLanguageVisual,
  type SupportedLanguage,
} from '@/lib/i18n'

export interface LanguageSelectorProps {
  visualOnly?: boolean
  className?: string
}

export function LanguageSelector({ visualOnly = false, className = '' }: LanguageSelectorProps) {
  // Subscribe to language changes so the component re-renders
  useTranslation()

  const currentLang = getCurrentLanguage()

  function handleChange(lang: SupportedLanguage) {
    if (visualOnly) {
      changeLanguageVisual(lang)
    } else {
      persistLanguage(lang)
    }
  }

  return (
    <div className={className}>
      <Dropdown>
        <Dropdown.Trigger>
          <HeroButton
            variant="ghost"
            size="sm"
            aria-label="Select language"
          >
            <Globe className="h-5 w-5" />
            <span className="text-xs font-medium uppercase">{currentLang}</span>
          </HeroButton>
        </Dropdown.Trigger>
        <Dropdown.Popover placement="bottom end">
          <Dropdown.Menu
            selectionMode="single"
            selectedKeys={new Set([currentLang])}
            onAction={(key) => handleChange(key as SupportedLanguage)}
          >
            {LANGUAGE_OPTIONS.map((option) => (
              <Dropdown.Item key={option.code} id={option.code}>
                <div className="flex items-center gap-2">
                  <span>{option.flag}</span>
                  <span>{option.name}</span>
                </div>
              </Dropdown.Item>
            ))}
          </Dropdown.Menu>
        </Dropdown.Popover>
      </Dropdown>
    </div>
  )
}
