/**
 * Forgot Password Page - Uses AuthLayout for consistent split-panel design.
 *
 * Sends password reset link to the provided email address.
 */

import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Form } from '@heroui/react'
import { Mail, ArrowLeft } from 'lucide-react'
import AuthLayout from '@/layouts/AuthLayout'
import { InputField, FormErrorBanner, Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  errors?: Record<string, string>
}

export default function ForgotPassword({ errors = {} }: Props) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      email: '',
    },
    url: '/auth/forgot-password/',
    method: 'post',
  })

  return (
    <AuthLayout
      title={t('auth.forgotPassword.title')}
      subtitle={t('auth.forgotPassword.description')}
    >
      <Head title={t('auth.forgotPassword.pageTitle')} />

      <Form
        onSubmit={submit}
        validationErrors={errors}
        validationBehavior="aria"
        className="space-y-6"
      >
        <FormErrorBanner message={errors.__all__} />

        <InputField
          name="email"
          label={t('auth.forgotPassword.emailLabel')}
          type="email"
          placeholder={t('auth.forgotPassword.emailPlaceholder')}
          value={data.email}
          onChange={(e) => setData('email', e.target.value)}
          error={errors.email}
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
          loadingText={t('auth.forgotPassword.submitting')}
          isDisabled={!data.email}
        >
          {t('auth.forgotPassword.submit')}
        </Button>

        {/* Back to login */}
        <div className="flex justify-center">
          <Link
            href="/auth/login/"
            className="inline-flex items-center gap-2 text-sm text-primary hover:opacity-80"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('auth.forgotPassword.backToLogin')}
          </Link>
        </div>
      </Form>
    </AuthLayout>
  )
}
