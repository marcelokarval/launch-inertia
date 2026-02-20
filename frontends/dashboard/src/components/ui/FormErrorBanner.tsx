/**
 * FormErrorBanner - Flash-style error banner using HeroUI Alert compound pattern.
 */

import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import { Alert, CloseButton } from '@heroui/react'
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
    <Alert
      status="danger"
      className={`animate-in fade-in slide-in-from-top-2 duration-300 ${className}`}
    >
      <Alert.Indicator>
        <AlertCircle className="h-4 w-4" />
      </Alert.Indicator>
      <Alert.Content>
        <Alert.Description>{message}</Alert.Description>
      </Alert.Content>
      {dismissible && (
        <CloseButton
          onPress={() => setDismissed(true)}
          className="flex-shrink-0"
          aria-label={t('actions.dismiss')}
        />
      )}
    </Alert>
  )
}
