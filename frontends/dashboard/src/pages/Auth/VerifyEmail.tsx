/**
 * Auth Email Verification Page (standalone, no login required).
 *
 * Two-step flow:
 * 1. Enter email -> sends verification code
 * 2. Enter 6-digit OTP -> verifies email -> redirects to login
 */

import { useState, useEffect } from 'react'
import { Head, Link } from '@inertiajs/react'
import { Form, TextField, Input, Label, FieldError, Button as HeroButton } from '@heroui/react'
import { Button } from '@/components/ui'
import { OtpInput } from '@/components/shared/OtpInput'
import { Mail, RefreshCw, ArrowLeft, ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  step?: 'email' | 'code'
  email?: string
  errors?: Record<string, string[]>
}

const RESEND_COOLDOWN = 60

export default function VerifyEmail({ step = 'email', email = '', errors = {} }: Props) {
  if (step === 'code') {
    return <CodeStep email={email} errors={errors} />
  }

  return <EmailStep email={email} errors={errors} />
}

/* ── Step 1: Enter email ─────────────────────────────────────────── */

function EmailStep({ email, errors }: { email: string; errors: Record<string, string[]> }) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      action: 'send',
      email: email || '',
    },
    url: '/auth/verify-email/',
    method: 'post',
  })

  return (
    <>
      <Head title={t('auth.verifyEmail.pageTitle', 'Verify Email')} />

      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="w-full max-w-md space-y-6">
          {/* Back to login */}
          <Link
            href="/auth/login/"
            className="inline-flex items-center gap-2 text-sm text-default-500 hover:text-primary transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('auth.verifyEmail.backToLogin', 'Back to login')}
          </Link>

          <div className="bg-content1 rounded-xl shadow-lg border border-default-200 p-8">
            <div className="text-center space-y-3 mb-8">
              <div className="mx-auto w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                <Mail className="w-7 h-7 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-foreground">
                {t('auth.verifyEmail.title', 'Verify your email')}
              </h1>
              <p className="text-sm text-default-500">
                {t('auth.verifyEmail.enterEmailDescription', 'Enter your email address and we\'ll send you a verification code.')}
              </p>
            </div>

            <Form onSubmit={submit} validationErrors={errors.email ? { email: errors.email[0] } : undefined} className="space-y-6">
              <TextField name="email" className="space-y-2" isRequired>
                <Label>{t('auth.verifyEmail.emailLabel', 'Email')}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="email"
                    value={data.email}
                    onChange={(e) => setData('email', e.target.value)}
                    placeholder={t('auth.verifyEmail.emailPlaceholder', 'your@email.com')}
                    className="pl-10"
                  />
                </div>
                <FieldError />
              </TextField>

              <Button
                type="submit"
                variant="primary"
                fullWidth
                isLoading={isSubmitting}
                loadingText={t('auth.verifyEmail.sending', 'Sending...')}
                isDisabled={!data.email}
              >
                {t('auth.verifyEmail.sendCode', 'Send verification code')}
              </Button>
            </Form>
          </div>
        </div>
      </div>
    </>
  )
}

/* ── Step 2: Enter OTP code ──────────────────────────────────────── */

function CodeStep({ email, errors }: { email: string; errors: Record<string, string[]> }) {
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
    resendSubmit()
  }

  const codeError = errors.verification_code?.[0]
  const isCodeComplete = code.length === 6

  return (
    <>
      <Head title={t('auth.verifyEmail.pageTitle', 'Verify Email')} />

      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="w-full max-w-md space-y-6">
          {/* Back to login */}
          <Link
            href="/auth/login/"
            className="inline-flex items-center gap-2 text-sm text-default-500 hover:text-primary transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('auth.verifyEmail.backToLogin', 'Back to login')}
          </Link>

          <div className="bg-content1 rounded-xl shadow-lg border border-default-200 p-8">
            <div className="text-center space-y-3 mb-8">
              <div className="mx-auto w-14 h-14 rounded-full bg-success/10 flex items-center justify-center">
                <ShieldCheck className="w-7 h-7 text-success" />
              </div>
              <h1 className="text-2xl font-bold text-foreground">
                {t('auth.verifyEmail.codeTitle', 'Enter verification code')}
              </h1>
              <p className="text-sm text-default-500">
                {t('auth.verifyEmail.codeSentTo', 'We sent a 6-digit code to')}{' '}
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
                loadingText={t('auth.verifyEmail.verifying', 'Verifying...')}
                isDisabled={!isCodeComplete}
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
                  ? t('auth.verifyEmail.resendCountdown', 'Resend in {{seconds}}s', { seconds: resendCountdown })
                  : t('auth.verifyEmail.resend', 'Resend code')}
              </HeroButton>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
