/**
 * PasswordInput - Password field with visibility toggle and optional strength indicator.
 */

import { useState, useMemo } from 'react'
import { TextField, Input, Label, FieldError, Button as HeroButton } from '@heroui/react'
import { Eye, EyeOff, Lock } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export interface PasswordInputProps {
  name: string
  label?: string
  placeholder?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  error?: string
  required?: boolean
  autoComplete?: string
  disabled?: boolean
  className?: string
  showStrength?: boolean
}

type StrengthLevel = 'weak' | 'medium' | 'strong' | 'very-strong'

interface StrengthInfo {
  level: StrengthLevel
  labelKey: string
  color: string
  width: string
}

function getPasswordStrength(password: string): StrengthInfo {
  let score = 0
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[^a-zA-Z0-9]/.test(password)) score++

  if (score <= 1)
    return { level: 'weak', labelKey: 'passwordInput.strength.weak', color: 'bg-danger', width: 'w-1/4' }
  if (score <= 2)
    return { level: 'medium', labelKey: 'passwordInput.strength.medium', color: 'bg-warning', width: 'w-2/4' }
  if (score <= 3)
    return { level: 'strong', labelKey: 'passwordInput.strength.strong', color: 'bg-success', width: 'w-3/4' }
  return { level: 'very-strong', labelKey: 'passwordInput.strength.veryStrong', color: 'bg-success', width: 'w-full' }
}

export function PasswordInput({
  name,
  label,
  placeholder = '••••••••',
  value,
  onChange,
  error,
  required = false,
  autoComplete,
  disabled = false,
  className = '',
  showStrength = false,
}: PasswordInputProps) {
  const { t } = useTranslation('components')
  const [showPassword, setShowPassword] = useState(false)
  const strength = useMemo(
    () => (showStrength && value ? getPasswordStrength(value) : null),
    [showStrength, value],
  )

  return (
    <div className={`space-y-2 w-full ${className}`}>
      <TextField
        name={name}
        isInvalid={!!error}
        isRequired={required}
        isDisabled={disabled}
        className="space-y-2 w-full"
      >
        {label && (
          <Label className="text-sm font-medium text-default-700">
            {label}
          </Label>
        )}
        <div className="relative w-full">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
          <Input
            type={showPassword ? 'text' : 'password'}
            placeholder={placeholder}
            autoComplete={autoComplete}
            value={value}
            onChange={onChange}
            className="w-full pl-10 pr-10 font-mono tracking-wider bg-default-100 border-default-200"
          />
          <HeroButton
            variant="ghost"
            size="sm"
            isIconOnly
            onPress={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-default-400 hover:text-default-600 min-w-0 h-auto p-0"
            aria-label={showPassword ? t('passwordInput.hidePassword') : t('passwordInput.showPassword')}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </HeroButton>
        </div>
        {error ? (
          <p className="text-sm text-danger" role="alert">{error}</p>
        ) : (
          <FieldError />
        )}
      </TextField>

      {/* Strength meter */}
      {strength && (
        <div className="space-y-1">
          <div className="h-1.5 w-full bg-default-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${strength.color} ${strength.width}`}
            />
          </div>
          <p className="text-xs text-default-500">
            {t('passwordInput.strengthLabel')}{' '}
            <span className="font-medium">{t(strength.labelKey)}</span>
          </p>
        </div>
      )}
    </div>
  )
}
