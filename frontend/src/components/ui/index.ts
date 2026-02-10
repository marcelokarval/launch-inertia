/**
 * UI Components - Re-exports
 *
 * Custom components built on top of HeroUI v3.
 * Also re-exports native HeroUI components and styling utilities.
 *
 * @see https://v3.heroui.com/docs/react/getting-started/quick-start
 */

// ---------------------------------------------------------------------------
// Custom UI Components
// ---------------------------------------------------------------------------
export { Button } from './Button'
export type { ButtonProps, ButtonVariants } from './Button'

export { InputField } from './InputField'
export type { InputFieldProps } from './InputField'

export { PasswordInput } from './PasswordInput'
export type { PasswordInputProps } from './PasswordInput'

export { FormErrorBanner } from './FormErrorBanner'
export type { FormErrorBannerProps } from './FormErrorBanner'

export { ThemeToggle } from './ThemeToggle'
export type { ThemeToggleProps } from './ThemeToggle'

export { LanguageSelector } from './LanguageSelector'
export type { LanguageSelectorProps } from './LanguageSelector'

// ---------------------------------------------------------------------------
// HeroUI v3 Native Re-exports
// ---------------------------------------------------------------------------
export {
  // Forms - Compound Components
  Form,
  TextField,
  Input,
  Label,
  Description,
  FieldError,
  TextArea,
  SearchField,

  // Form Controls
  Checkbox,
  CheckboxGroup,
  Radio,
  RadioGroup,
  Select,
  Switch,
  Slider,

  // Feedback
  Spinner,

  // Overlays
  Modal,
  Popover,
  Tooltip,
  Dropdown,

  // Navigation
  Tabs,
  Tab,
  Link,
  Breadcrumbs,

  // Data Display
  Avatar,
  Chip,
  Accordion,
  AccordionItem,

  // Date & Time
  Calendar,

  // Misc
  Autocomplete,
} from '@heroui/react'

// Re-export styling utilities
export { tv, type VariantProps } from '@heroui/styles'
