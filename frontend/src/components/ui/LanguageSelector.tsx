/**
 * LanguageSelector - Dropdown to switch between supported languages.
 *
 * Props:
 * - visualOnly: if true, changes language without persisting to localStorage
 *   (used on login page where the user may not be the account owner).
 * - className: optional extra classes
 */

import { Globe } from 'lucide-react'
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
    <div className={`relative group ${className}`}>
      <button
        type="button"
        className="flex items-center gap-1.5 p-2 rounded-lg text-default-500 hover:bg-default-100 hover:text-default-700 transition-colors"
        aria-label="Select language"
      >
        <Globe className="h-5 w-5" />
        <span className="text-xs font-medium uppercase">{currentLang}</span>
      </button>

      {/* Dropdown */}
      <div className="absolute right-0 top-full mt-1 w-40 py-1 bg-content1 rounded-lg shadow-lg border border-default-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
        {LANGUAGE_OPTIONS.map((option) => (
          <button
            key={option.code}
            type="button"
            onClick={() => handleChange(option.code)}
            className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 transition-colors ${
              currentLang === option.code
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-default-700 hover:bg-default-100'
            }`}
          >
            <span>{option.flag}</span>
            <span>{option.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
