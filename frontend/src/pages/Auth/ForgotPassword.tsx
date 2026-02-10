import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Card, TextField, Input, Label, FieldError, Form } from '@heroui/react'
import { Button } from '@/components/ui'
import { Mail, ArrowLeft } from 'lucide-react'
import { useAppForm } from '@/hooks/useAppForm'

export default function ForgotPassword() {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      email: '',
    },
    url: '/auth/forgot-password/',
    method: 'post',
  })

  return (
    <>
      <Head title={t('auth.forgotPassword.pageTitle')} />

      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md shadow-xl">
          <Card.Header className="p-8 pb-6">
            <Card.Title className="text-2xl font-bold text-center">
              {t('auth.forgotPassword.title')}
            </Card.Title>
            <Card.Description className="text-center text-default-500">
              {t('auth.forgotPassword.description')}
            </Card.Description>
          </Card.Header>

          <Card.Content className="p-8 pt-0">
            <Form onSubmit={submit} className="space-y-6">
              <TextField name="email" className="space-y-2 w-full">
                <Label>{t('auth.forgotPassword.emailLabel')}</Label>
                <div className="relative w-full">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="email"
                    placeholder={t('auth.forgotPassword.emailPlaceholder')}
                    required
                    value={data.email}
                    onChange={(e) => setData('email', e.target.value)}
                    className="w-full pl-10"
                  />
                </div>
                <FieldError />
              </TextField>

              <Button
                type="submit"
                variant="primary"
                fullWidth
                isLoading={isSubmitting}
                loadingText={t('auth.forgotPassword.submitting')}
                isDisabled={!data.email}
              >
                {t('auth.forgotPassword.submit')}
              </Button>
            </Form>
          </Card.Content>

          <Card.Footer className="flex justify-center p-6 pt-0">
            <Link
              href="/auth/login/"
              className="flex items-center gap-2 text-sm text-primary hover:opacity-80"
            >
              <ArrowLeft className="h-4 w-4" />
              {t('auth.forgotPassword.backToLogin')}
            </Link>
          </Card.Footer>
        </Card>
      </div>
    </>
  )
}
