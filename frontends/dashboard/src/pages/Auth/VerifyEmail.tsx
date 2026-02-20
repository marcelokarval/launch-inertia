/**
 * Auth Email Verification Page (standalone, no login required).
 *
 * Two-step flow:
 * 1. Enter email -> sends verification code
 * 2. Enter 6-digit OTP -> verifies email -> redirects to login
 *
 * Step 2 is extracted to VerifyEmailCode.tsx to stay under 150 lines.
 */

import { Head, Link } from '@inertiajs/react'
import { Form } from '@heroui/react'
import { Mail, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import AuthLayout from '@/layouts/AuthLayout'
import { InputField, FormErrorBanner, Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'
import { VerifyEmailCode } from './VerifyEmailCode'

interface Props {
  step?: 'email' | 'code'
  email?: string
  errors?: Record<string, string[]>
}

export default function VerifyEmail({
  step = 'email',
  email = '',
  errors = {},
}: Props) {
  if (step === 'code') {
    return <VerifyEmailCode email={email} errors={errors} />
  }

  return <EmailStep email={email} errors={errors} />
}

/* ── Step 1: Enter email ─────────────────────────────────────────── */

function EmailStep({
  email,
  errors,
}: {
  email: string
  errors: Record<string, string[]>
}) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      action: 'send',
      email: email || '',
    },
    url: '/auth/verify-email/',
    method: 'post',
  })

  const emailError = errors.email?.[0]

  return (
    <AuthLayout
      title={t('auth.verifyEmail.title', 'Verify your email')}
      subtitle={t(
        'auth.verifyEmail.enterEmailDescription',
        "Enter your email address and we'll send you a verification code.",
      )}
    >
      <Head title={t('auth.verifyEmail.pageTitle', 'Verify Email')} />

      <div className="flex justify-center mb-6">
        <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
          <Mail className="w-7 h-7 text-primary" />
        </div>
      </div>

      <Form
        onSubmit={submit}
        validationErrors={emailError ? { email: emailError } : undefined}
        className="space-y-6"
      >
        <FormErrorBanner message={emailError} />

        <InputField
          name="email"
          label={t('auth.verifyEmail.emailLabel', 'Email')}
          type="email"
          placeholder={t('auth.verifyEmail.emailPlaceholder', 'your@email.com')}
          value={data.email}
          onChange={(e) => setData('email', e.target.value)}
          error={emailError}
          required
          autoComplete="email"
          startContent={<Mail className="h-4 w-4" />}
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isSubmitting}
          loadingText={t('auth.verifyEmail.sending', 'Sending...')}
          isDisabled={!data.email}
        >
          {t('auth.verifyEmail.sendCode', 'Send verification code')}
        </Button>

        {/* Back to login */}
        <div className="flex justify-center">
          <Link
            href="/auth/login/"
            className="inline-flex items-center gap-2 text-sm text-primary hover:opacity-80"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('auth.verifyEmail.backToLogin', 'Back to login')}
          </Link>
        </div>
      </Form>
    </AuthLayout>
  )
}
