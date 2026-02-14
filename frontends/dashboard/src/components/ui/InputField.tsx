/**
 * InputField - Simplified text input with error display.
 *
 * Wraps HeroUI TextField with a built-in error prop
 * that auto-applies error styling.
 */

import { TextField, Input, Label, FieldError } from '@heroui/react'
import type { ReactNode } from 'react'

export interface InputFieldProps {
  name: string
  label?: string
  type?: string
  placeholder?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  error?: string
  required?: boolean
  autoComplete?: string
  disabled?: boolean
  className?: string
  startContent?: ReactNode
  endContent?: ReactNode
}

export function InputField({
  name,
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  required = false,
  autoComplete,
  disabled = false,
  className = '',
  startContent,
  endContent,
}: InputFieldProps) {
  return (
    <TextField
      name={name}
      isInvalid={!!error}
      isRequired={required}
      isDisabled={disabled}
      className={`space-y-2 w-full ${className}`}
    >
      {label && (
        <Label className="text-sm font-medium text-default-700">
          {label}
        </Label>
      )}
      <div className="relative w-full">
        {startContent && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-default-400 z-10">
            {startContent}
          </div>
        )}
        <Input
          type={type}
          placeholder={placeholder}
          autoComplete={autoComplete}
          value={value}
          onChange={onChange}
          className={`w-full ${startContent ? 'pl-10' : ''} ${endContent ? 'pr-10' : ''} bg-default-100 border-default-200`}
        />
        {endContent && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 z-10">
            {endContent}
          </div>
        )}
      </div>
      {error ? (
        <p className="text-sm text-danger">{error}</p>
      ) : (
        <FieldError />
      )}
    </TextField>
  )
}
