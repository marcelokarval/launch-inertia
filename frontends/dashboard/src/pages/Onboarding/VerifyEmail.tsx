/**
 * Onboarding Step 1: Email Verification via 6-digit OTP
 */

import { useState, useEffect } from 'react'
import { Head, router } from '@inertiajs/react'
import { Form, Button as HeroButton } from '@heroui/react'
import { Button } from '@/components/ui'
import { OtpInput } from '@/components/shared/OtpInput'
import { Mail, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import OnboardingLayout from '@/layouts/OnboardingLayout'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  email?: string
  errors?: Record<string, string[]>
}

const RESEND_COOLDOWN = 60

export default function VerifyEmail({ email, errors = {} }: Props) {
  const { t } = useTranslation()
  const [code, setCode] = useState('')
  const [resendCountdown, setResendCountdown] = useState(0)

  const { setData, submit, isSubmitting } = useAppForm({
    initialData: {
      verification_code: '',
    },
    url: '/onboarding/verify-email/',
    method: 'post',
  })

  // Countdown timer for resend
  useEffect(() => {
    if (resendCountdown <= 0) return
    const timer = setInterval(() => {
      setResendCountdown((prev) => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCountdown])

  function handleCodeChange(newCode: string) {
    setCode(newCode)
    setData('verification_code', newCode)
  }

  function handleResend() {
    if (resendCountdown > 0) return
    setResendCountdown(RESEND_COOLDOWN)
    router.post('/onboarding/resend-verification/', {}, { forceFormData: true })
  }

  const codeError = errors.verification_code?.[0]
  const isCodeComplete = code.length === 6

  return (
    <OnboardingLayout currentStep={1} title={t('onboarding.verifyEmail.title')}>
      <Head title={t('onboarding.verifyEmail.pageTitle')} />

      <div className="space-y-6">
        <div className="text-center space-y-2">
           <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <Mail className="w-6 h-6 text-primary" />
          </div>
          <p className="text-sm text-default-600">
            {t('onboarding.verifyEmail.instruction')}{' '}
            <span className="font-medium text-foreground">{email}</span>
          </p>
        </div>

        <Form onSubmit={submit} className="space-y-6">
          <OtpInput onChange={handleCodeChange} error={codeError} />

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={isSubmitting}
            loadingText={t('onboarding.verifyEmail.submitting')}
            isDisabled={!isCodeComplete}
          >
            {t('onboarding.verifyEmail.submit')}
          </Button>
        </Form>

        {/* Resend */}
        <div className="text-center">
          <HeroButton
            variant="ghost"
            size="sm"
            onPress={handleResend}
            isDisabled={resendCountdown > 0}
            className={resendCountdown > 0 ? 'text-default-400' : 'text-primary'}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {resendCountdown > 0
              ? t('onboarding.verifyEmail.resendCountdown', { seconds: resendCountdown })
              : t('onboarding.verifyEmail.resendPrompt')}
          </HeroButton>
        </div>
      </div>
    </OnboardingLayout>
  )
}
