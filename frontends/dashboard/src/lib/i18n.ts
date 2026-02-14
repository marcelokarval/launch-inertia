/**
 * i18n configuration for Launch.
 *
 * Uses i18next with HTTP backend (loads JSON at runtime from /static/locales/)
 * and browser language detection.
 *
 * 3 supported languages: pt (default), en, es
 * 3 namespaces: translation (default), common (shared UI), components
 */
import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import HttpBackend from 'i18next-http-backend'
import { initReactI18next } from 'react-i18next'

// ── Constants ──────────────────────────────────────────────────────────────────

export const I18N_STORAGE_KEY = 'launch-language'
export const DEFAULT_LANGUAGE = 'pt'
export const SUPPORTED_LANGUAGES = ['pt', 'en', 'es'] as const
export const I18N_NAMESPACES = ['translation', 'common', 'components'] as const

export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export interface LanguageOption {
  code: SupportedLanguage
  name: string
  flag: string
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { code: 'pt', name: 'Portugues', flag: '🇧🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Espanol', flag: '🇪🇸' },
]

// ── Initialization ─────────────────────────────────────────────────────────────

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // Languages
    supportedLngs: [...SUPPORTED_LANGUAGES],
    fallbackLng: DEFAULT_LANGUAGE,
    load: 'languageOnly', // "pt-BR" → "pt"
    nonExplicitSupportedLngs: true,

    // Namespaces
    ns: [...I18N_NAMESPACES],
    defaultNS: 'translation',
    fallbackNS: 'common',

    // Backend: load from Django static
    backend: {
      loadPath: '/static/locales/{{lng}}/{{ns}}.json',
    },

    // Detection: localStorage first, then navigator
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      lookupLocalStorage: I18N_STORAGE_KEY,
      caches: [], // Manual persistence only
    },

    // Behavior
    interpolation: {
      escapeValue: false, // React handles XSS
    },
    react: {
      useSuspense: false, // Avoid Suspense boundary requirement
    },
    returnNull: false,
    returnEmptyString: false,
  })

// ── Language Utilities ─────────────────────────────────────────────────────────

/**
 * Change language and persist to localStorage.
 * Use after login / on profile settings.
 */
export function persistLanguage(lang: SupportedLanguage): void {
  localStorage.setItem(I18N_STORAGE_KEY, lang)
  i18n.changeLanguage(lang)
}

/**
 * Change language visually without persisting.
 * Use on the login page (user might not be the account owner).
 */
export function changeLanguageVisual(lang: SupportedLanguage): void {
  i18n.changeLanguage(lang)
}

/**
 * Get the persisted language from localStorage.
 */
export function getPersistedLanguage(): SupportedLanguage | null {
  const stored = localStorage.getItem(I18N_STORAGE_KEY)
  if (stored && SUPPORTED_LANGUAGES.includes(stored as SupportedLanguage)) {
    return stored as SupportedLanguage
  }
  return null
}

/**
 * Get the current active language.
 */
export function getCurrentLanguage(): SupportedLanguage {
  const lang = i18n.language?.split('-')[0] as SupportedLanguage
  return SUPPORTED_LANGUAGES.includes(lang) ? lang : DEFAULT_LANGUAGE
}

export default i18n
