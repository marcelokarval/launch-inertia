/**
 * FormErrorBanner - Flash-style error banner with optional dismiss.
 */

import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import { CloseButton } from '@heroui/react'
import { useTranslation } from 'react-i18next'

export interface FormErrorBannerProps {
  message?: string | null
  dismissible?: boolean
  className?: string
}

export function FormErrorBanner({
  message,
  dismissible = true,
  className = '',
}: FormErrorBannerProps) {
  const { t } = useTranslation('common')
  const [dismissed, setDismissed] = useState(false)

  if (!message || dismissed) return null

  return (
    <div
      className={`animate-in fade-in slide-in-from-top-2 duration-300 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm ${className}`}
      role="alert"
    >
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        <span className="flex-1">{message}</span>
        {dismissible && (
          <CloseButton
            onPress={() => setDismissed(true)}
            className="flex-shrink-0 text-danger-400 hover:text-danger-600"
            aria-label={t('actions.dismiss')}
          />
        )}
      </div>
    </div>
  )
}
