/**
 * Delinquent Page - Shown when user has a payment issue.
 *
 * Standalone layout (no DashboardLayout).
 * Links to billing portal and provides a logout option.
 */

import { Head, router } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Link as HeroLink } from '@heroui/react'
import { AlertTriangle, CreditCard, LogOut } from 'lucide-react'
import { Button } from '@/components/ui'

interface Props {
  message?: string
}

export default function Delinquent({ message }: Props) {
  const { t } = useTranslation()

  const openPortal = () => {
    router.post('/app/billing/portal/', {}, { forceFormData: true })
  }

  return (
    <>
      <Head title={t('delinquent.pageTitle')} />

      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center space-y-8">
          {/* Warning icon */}
          <div className="flex justify-center">
             <div className="p-4 rounded-full bg-warning/10">
              <AlertTriangle className="h-12 w-12 text-warning" />
            </div>
          </div>

          {/* Message */}
          <div className="space-y-3">
            <h1 className="text-2xl font-bold text-foreground">
              {t('delinquent.title')}
            </h1>
            <p className="text-default-600">
              {message || t('delinquent.defaultMessage')}
            </p>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onPress={openPortal}
            >
              <CreditCard className="h-5 w-5" />
              {t('delinquent.goToBilling')}
            </Button>

            <Button
              variant="outline"
              size="md"
              fullWidth
              onPress={() => router.post('/auth/logout/', {}, { forceFormData: true })}
            >
              <LogOut className="h-4 w-4" />
              {t('delinquent.logout')}
            </Button>
          </div>

          {/* Footer */}
          <p className="text-sm text-default-400">
            {t('delinquent.needHelp')}{' '}
            <HeroLink
              href="mailto:support@botrei.com"
              className="text-primary hover:opacity-80 font-medium"
            >
              {t('delinquent.contactSupport')}
            </HeroLink>
          </p>
        </div>
      </div>
    </>
  )
}
