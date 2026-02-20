/**
 * Login Page - Uses AuthLayout for consistent split-panel design.
 *
 * Fields: username (email), password, remember_me
 * Backend expects 'username' field (Django AuthenticationForm).
 */

import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Form, Checkbox, Alert } from '@heroui/react'
import { User, ArrowRight, AlertCircle } from 'lucide-react'
import AuthLayout from '@/layouts/AuthLayout'
import { InputField, PasswordInput, FormErrorBanner, Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  errors?: Record<string, string>
  needs_verification?: boolean
  verification_email?: string | null
}

export default function Login({
  errors = {},
  needs_verification = false,
  verification_email = null,
}: Props) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      username: '',
      password: '',
      remember_me: false as boolean,
    },
    url: '/auth/login/',
    method: 'post',
  })

  return (
    <AuthLayout
      title={t('auth.login.welcomeBack')}
      subtitle={t('auth.login.description')}
    >
      <Head title={t('auth.login.pageTitle')} />

      <Form
        onSubmit={submit}
        validationErrors={errors}
        validationBehavior="aria"
        className="space-y-6"
      >
        {/* General error */}
        <FormErrorBanner message={errors.__all__} />

        {/* Verification notice */}
        {errors.__all__ && needs_verification && (
          <Alert status="warning">
            <Alert.Indicator>
              <AlertCircle className="h-4 w-4" />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Description>
                <Link
                  href={`/auth/verify-email/${verification_email ? `?email=${encodeURIComponent(verification_email)}` : ''}`}
                  className="inline-flex items-center gap-1 font-medium text-primary hover:opacity-80"
                >
                  {t('auth.login.verifyEmailLink', 'Verify your email now')}
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Alert.Description>
            </Alert.Content>
          </Alert>
        )}

        {/* Email (sent as 'username' to Django) */}
        <InputField
          name="username"
          label={t('auth.login.emailLabel')}
          type="email"
          placeholder={t('auth.login.emailPlaceholder')}
          value={data.username}
          onChange={(e) => setData('username', e.target.value)}
          error={errors.username}
          required
          autoComplete="email"
          startContent={<User className="h-4 w-4" />}
        />

        {/* Password */}
        <div className="space-y-1">
          <PasswordInput
            name="password"
            label={t('auth.login.passwordLabel')}
            value={data.password}
            onChange={(e) => setData('password', e.target.value)}
            error={errors.password}
            required
            autoComplete="current-password"
          />
          <div className="flex justify-end">
            <Link
              href="/auth/forgot-password/"
              className="text-xs text-default-500 hover:text-primary transition-colors"
            >
              {t('auth.login.forgotPassword')}
            </Link>
          </div>
        </div>

        {/* Remember me */}
        <div className="space-y-2">
          <Checkbox
            isSelected={data.remember_me}
            onChange={(isSelected) => setData('remember_me', isSelected)}
          >
            <span className="text-sm text-default-600">
              {t('auth.login.rememberMe')}
            </span>
          </Checkbox>
          {data.remember_me && (
            <p className="text-xs text-default-400 ml-6">
              {t('auth.login.rememberMeHelp')}
            </p>
          )}
        </div>

        {/* Submit */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isSubmitting}
          loadingText={t('auth.login.submitting')}
          isDisabled={!data.username || !data.password || data.password.length < 8}
        >
          <span>{t('auth.login.submit')}</span>
          <ArrowRight className="h-4 w-4" />
        </Button>

        {/* Register link */}
        <p className="text-center text-sm text-default-500">
          {t('auth.login.noAccount')}{' '}
          <Link
            href="/auth/register/"
            className="text-primary hover:opacity-80 font-medium"
          >
            {t('auth.login.signUp')}
          </Link>
        </p>
      </Form>
    </AuthLayout>
  )
}
