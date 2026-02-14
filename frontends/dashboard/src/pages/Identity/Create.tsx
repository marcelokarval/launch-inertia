import { Head, Link } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, TextField, Input, Label, FieldError, Form } from '@heroui/react'
import { Button } from '@/components/ui'
import { User, Mail, Phone, ArrowLeft, Info } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  errors?: Record<string, string>
}

export default function IdentityCreate({ errors = {} }: Props) {
  const { t } = useTranslation()
  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      email: '',
      phone: '',
      display_name: '',
    },
    url: '/app/identities/create/',
    method: 'post',
  })

  const hasContactInfo = data.email.trim() !== '' || data.phone.trim() !== ''

  return (
    <DashboardLayout title={t('identities.create.title', 'Import Identity')}>
      <Head title={t('identities.create.pageTitle', 'Import Identity')} />

      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/app/identities/"
            className="p-2 rounded-lg hover:bg-default-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              {t('identities.create.title', 'Import Identity')}
            </h2>
            <p className="text-default-500">
              {t('identities.create.description', 'Import a new identity by providing at least an email or phone.')}
            </p>
          </div>
        </div>

        <Card>
          <Card.Content className="p-6">
            <Form
              onSubmit={submit}
              validationErrors={errors}
              className="space-y-6"
            >
              {/* Requirement notice */}
              <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/10">
                <Info className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                <p className="text-sm text-default-600">
                  {t('identities.create.requirementNote', 'At least an email or phone number is required to create an identity.')}
                </p>
              </div>

              <TextField name="email" className="space-y-2">
                <Label>{t('identities.create.emailLabel', 'Email')}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="email"
                    value={data.email}
                    onChange={(e) => setData('email', e.target.value)}
                    className="pl-10"
                    placeholder={t('identities.create.emailPlaceholder', 'contact@example.com')}
                  />
                </div>
                <FieldError />
              </TextField>

              <TextField name="phone" className="space-y-2">
                <Label>{t('identities.create.phoneLabel', 'Phone')}</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="tel"
                    value={data.phone}
                    onChange={(e) => setData('phone', e.target.value)}
                    className="pl-10"
                    placeholder={t('identities.create.phonePlaceholder', '+55 11 99999-0000')}
                  />
                </div>
                <FieldError />
              </TextField>

              <TextField name="display_name" className="space-y-2">
                <Label>{t('identities.create.displayNameLabel', 'Display Name')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="text"
                    value={data.display_name}
                    onChange={(e) => setData('display_name', e.target.value)}
                    className="pl-10"
                    placeholder={t('identities.create.displayNamePlaceholder', 'John Doe (optional)')}
                  />
                </div>
                <FieldError />
              </TextField>

              <div className="flex items-center gap-4 pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  loadingText={t('identities.create.submitting', 'Importing...')}
                  isDisabled={!hasContactInfo}
                >
                  {t('identities.create.submit', 'Import')}
                </Button>
                <Link href="/app/identities/">
                  <Button type="button" variant="secondary">
                    {t('identities.create.cancel', 'Cancel')}
                  </Button>
                </Link>
              </div>
            </Form>
          </Card.Content>
        </Card>
      </div>
    </DashboardLayout>
  )
}
