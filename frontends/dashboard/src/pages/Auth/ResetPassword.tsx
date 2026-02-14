/**
 * ResetPassword Page - Set a new password via token.
 *
 * Receives `token` prop from backend.
 * POSTs to /auth/reset-password/{token}/ with forceFormData: true.
 */

import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Form } from '@heroui/react'
import { ArrowLeft } from 'lucide-react'
import AuthLayout from '@/layouts/AuthLayout'
import { PasswordInput, FormErrorBanner, Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  token: string
  errors?: Record<string, string>
}

export default function ResetPassword({ token, errors = {} }: Props) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      new_password: '' as string,
      new_password_confirmation: '' as string,
      verification_code: token as string,
    },
    url: `/auth/reset-password/${token}/`,
    method: 'post',
  })

  const allFilled = data.new_password && data.new_password_confirmation

  return (
    <AuthLayout
      title={t('auth.resetPassword.title')}
      subtitle={t('auth.resetPassword.subtitle')}
    >
      <Head title={t('auth.resetPassword.pageTitle')} />

      <Form
        onSubmit={submit}
        validationErrors={errors}
        validationBehavior="aria"
        className="space-y-6"
      >
        <FormErrorBanner message={errors.__all__} />

        <PasswordInput
          name="new_password"
          label={t('auth.resetPassword.newPasswordLabel')}
          value={data.new_password as string}
          onChange={(e) => setData('new_password', e.target.value)}
          error={errors.new_password}
          required
          autoComplete="new-password"
          showStrength
        />

        <PasswordInput
          name="new_password_confirmation"
          label={t('auth.resetPassword.confirmPasswordLabel')}
          value={data.new_password_confirmation as string}
          onChange={(e) => setData('new_password_confirmation', e.target.value)}
          error={errors.new_password_confirmation}
          required
          autoComplete="new-password"
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isSubmitting}
          loadingText={t('auth.resetPassword.submitting')}
          isDisabled={!allFilled}
        >
          {t('auth.resetPassword.submit')}
        </Button>

        <div className="flex justify-center">
          <Link
            href="/auth/login/"
            className="flex items-center gap-2 text-sm text-primary hover:opacity-80"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('auth.resetPassword.backToLogin')}
          </Link>
        </div>
      </Form>
    </AuthLayout>
  )
}
