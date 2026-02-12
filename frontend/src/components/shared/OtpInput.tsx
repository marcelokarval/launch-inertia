/**
 * Shared OTP (One-Time Password) Input Component
 *
 * 6-digit code input with auto-focus, paste support, and backspace navigation.
 * Used by Auth/VerifyEmail and Onboarding/VerifyEmail.
 *
 * ACCEPTED EXCEPTION: Uses native `<input>` instead of HeroUI Input.
 * Reason: HeroUI has no single-digit OTP input component. This component
 * requires per-digit ref management, focus chaining, paste interception, and
 * `inputMode="numeric"` — wrapping each digit in a full HeroUI Input/TextField
 * would add unnecessary DOM overhead and break the focus-chain UX.
 */

import { useState, useRef, useEffect, useCallback } from 'react'

interface OtpInputProps {
  /** Number of digits (default: 6) */
  length?: number
  /** Called when the code value changes */
  onChange: (code: string) => void
  /** Validation error message */
  error?: string
  /** Auto-focus the first input on mount (default: true) */
  autoFocus?: boolean
}

export function OtpInput({ length = 6, onChange, error, autoFocus = true }: OtpInputProps) {
  const [digits, setDigits] = useState<string[]>(Array(length).fill(''))
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Auto-focus first input on mount
  useEffect(() => {
    if (autoFocus) {
      inputRefs.current[0]?.focus()
    }
  }, [autoFocus])

  const updateCode = useCallback(
    (newDigits: string[]) => {
      setDigits(newDigits)
      onChange(newDigits.join(''))
    },
    [onChange],
  )

  function handleDigitChange(index: number, value: string) {
    const digit = value.replace(/\D/g, '').slice(-1)
    const newDigits = [...digits]
    newDigits[index] = digit
    updateCode(newDigits)

    // Auto-focus next input
    if (digit && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length)
    if (pasted.length > 0) {
      const newDigits = [...digits]
      for (let i = 0; i < length; i++) {
        newDigits[i] = pasted[i] || ''
      }
      updateCode(newDigits)
      const focusIndex = Math.min(pasted.length, length - 1)
      inputRefs.current[focusIndex]?.focus()
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-center gap-2" onPaste={handlePaste}>
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(el) => {
              inputRefs.current[index] = el
            }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleDigitChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            className={`w-12 h-14 text-center text-xl font-semibold rounded-lg border-2 transition-colors
              focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
              ${error
                ? 'border-danger bg-danger/5'
                : 'border-default-300 bg-content1'
              }
              text-foreground`}
          />
        ))}
      </div>

      {error && (
        <p className="text-center text-sm text-danger">{error}</p>
      )}
    </div>
  )
}
