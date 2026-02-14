/**
 * Security Settings - Change password page.
 *
 * POSTs to /settings/security/ with forceFormData: true.
 */

import { Head } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Form } from '@heroui/react'
import { Shield } from 'lucide-react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { PasswordInput, FormErrorBanner, Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'
import type { SharedUser } from '@/types'

interface Props {
  user: SharedUser
  errors?: Record<string, string>
}

export default function Security({ user: _user, errors = {} }: Props) {
  const { t } = useTranslation()
  const { data, setData, submit, isSubmitting, reset } = useAppForm({
    initialData: {
      old_password: '' as string,
      new_password: '' as string,
      new_password_confirmation: '' as string,
    },
    url: '/app/settings/security/',
    method: 'post',
    onSuccess: () => {
      reset()
    },
  })

  const allFilled = data.old_password && data.new_password && data.new_password_confirmation

  return (
    <DashboardLayout title={t('settings.security.title')}>
      <Head title={t('settings.security.pageTitle')} />

      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Shield className="w-6 h-6 text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              {t('settings.security.title')}
            </h2>
          </div>
          <p className="text-default-500">
            {t('settings.security.description')}
          </p>
        </div>

        <div className="bg-content1 rounded-lg shadow-sm border border-default-200">
          <div className="p-6 border-b border-divider">
            <h3 className="text-lg font-semibold text-foreground">
              {t('settings.security.changePassword.title')}
            </h3>
            <p className="text-sm text-default-500 mt-1">
              {t('settings.security.changePassword.description')}
            </p>
          </div>

          <div className="p-6">
            <Form
              onSubmit={submit}
              validationErrors={errors}
              validationBehavior="aria"
              className="space-y-6"
            >
              <FormErrorBanner message={errors.__all__} />

              <PasswordInput
                name="old_password"
                label={t('settings.security.changePassword.currentLabel')}
                value={data.old_password as string}
                onChange={(e) => setData('old_password', e.target.value)}
                error={errors.old_password}
                required
                autoComplete="current-password"
              />

              <PasswordInput
                name="new_password"
                label={t('settings.security.changePassword.newLabel')}
                value={data.new_password as string}
                onChange={(e) => setData('new_password', e.target.value)}
                error={errors.new_password}
                required
                autoComplete="new-password"
                showStrength
              />

              <PasswordInput
                name="new_password_confirmation"
                label={t('settings.security.changePassword.confirmLabel')}
                value={data.new_password_confirmation as string}
                onChange={(e) =>
                  setData('new_password_confirmation', e.target.value)
                }
                error={errors.new_password_confirmation}
                required
                autoComplete="new-password"
              />

              <div className="pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  loadingText={t('settings.security.changePassword.submitting')}
                  isDisabled={!allFilled}
                >
                  {t('settings.security.changePassword.submit')}
                </Button>
              </div>
            </Form>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
