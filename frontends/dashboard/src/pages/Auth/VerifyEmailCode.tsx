/**
 * VerifyEmailCode - Step 2: Enter 6-digit OTP code.
 *
 * Extracted sub-component to keep VerifyEmail.tsx under 150 lines.
 */

import { useState, useEffect } from 'react'
import { Head } from '@inertiajs/react'
import { Form, Button as HeroButton } from '@heroui/react'
import { ShieldCheck, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import AuthLayout from '@/layouts/AuthLayout'
import { FormErrorBanner, Button } from '@/components/ui'
import { OtpInput } from '@/components/shared/OtpInput'
import { useAppForm } from '@/hooks/useAppForm'

const RESEND_COOLDOWN = 60

interface Props {
  email: string
  errors: Record<string, string[]>
}

export function VerifyEmailCode({ email, errors }: Props) {
  const { t } = useTranslation()
  const [code, setCode] = useState('')
  const [resendCountdown, setResendCountdown] = useState(0)

  const { setData, submit, isSubmitting } = useAppForm({
    initialData: {
      action: 'verify',
      email: email || '',
      verification_code: '',
    },
    url: '/auth/verify-email/',
    method: 'post',
  })

  const { submit: resendSubmit, isSubmitting: isResending } = useAppForm({
    initialData: {
      action: 'send',
      email: email || '',
    },
    url: '/auth/verify-email/',
    method: 'post',
  })

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
    resendSubmit()
  }

  const codeError = errors.verification_code?.[0]

  return (
    <AuthLayout
      title={t('auth.verifyEmail.codeTitle', 'Enter verification code')}
      subtitle={`${t('auth.verifyEmail.codeSentTo', 'We sent a 6-digit code to')} ${email}`}
    >
      <Head title={t('auth.verifyEmail.pageTitle', 'Verify Email')} />

      <div className="flex justify-center mb-6">
        <div className="w-14 h-14 rounded-full bg-success/10 flex items-center justify-center">
          <ShieldCheck className="w-7 h-7 text-success" />
        </div>
      </div>

      <Form onSubmit={submit} className="space-y-6">
        <FormErrorBanner message={codeError} />

        <OtpInput onChange={handleCodeChange} error={codeError} />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isSubmitting}
          loadingText={t('auth.verifyEmail.verifying', 'Verifying...')}
          isDisabled={code.length !== 6}
        >
          {t('auth.verifyEmail.verify', 'Verify email')}
        </Button>
      </Form>

      {/* Resend */}
      <div className="text-center mt-6">
        <HeroButton
          variant="ghost"
          size="sm"
          onPress={handleResend}
          isDisabled={resendCountdown > 0 || isResending}
          className={resendCountdown > 0 ? 'text-default-400' : 'text-primary'}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {resendCountdown > 0
            ? t('auth.verifyEmail.resendCountdown', 'Resend in {{seconds}}s', {
                seconds: resendCountdown,
              })
            : t('auth.verifyEmail.resend', 'Resend code')}
        </HeroButton>
      </div>
    </AuthLayout>
  )
}
