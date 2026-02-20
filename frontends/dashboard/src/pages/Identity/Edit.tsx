import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, TextField, Input, Label, FieldError, Form, TextArea } from '@heroui/react'
import { Button } from '@/components/ui'
import { User, ArrowLeft, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  identity: {
    id: string
    display_name: string
    operator_notes: string
    tag_ids: string[]
  }
  errors?: Record<string, string>
}

export default function IdentityEdit({ identity, errors = {} }: Props) {
  const { t } = useTranslation()
  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      display_name: identity.display_name || '',
      operator_notes: identity.operator_notes || '',
    },
    url: `/app/identities/${identity.id}/edit/`,
    method: 'post',
  })

  return (
    <DashboardLayout title={t('identities.edit.pageTitle', { name: identity.display_name || identity.id, defaultValue: 'Edit {{name}}' })}>
      <Head title={t('identities.edit.pageTitle', { name: identity.display_name || identity.id, defaultValue: 'Edit {{name}}' })} />

      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href={`/app/identities/${identity.id}/`}
            className="p-2 rounded-lg hover:bg-default-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              {t('identities.edit.title', 'Edit Identity')}
            </h2>
            <p className="text-default-500">
              {t('identities.edit.description', {
                name: identity.display_name || identity.id,
                defaultValue: 'Update operator fields for {{name}}',
              })}
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
              <TextField name="display_name" className="space-y-2">
                <Label>{t('identities.edit.displayNameLabel', 'Display Name')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="text"
                    value={data.display_name}
                    onChange={(e) => setData('display_name', e.target.value)}
                    className="pl-10"
                    placeholder={t('identities.edit.displayNamePlaceholder', 'e.g. John Doe')}
                  />
                </div>
                <FieldError />
              </TextField>

              <TextField name="operator_notes" className="space-y-2">
                <Label>
                  <span className="flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-default-400" />
                    {t('identities.edit.operatorNotesLabel', 'Operator Notes')}
                  </span>
                </Label>
                <TextArea
                  value={data.operator_notes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setData('operator_notes', e.target.value)}
                  placeholder={t('identities.edit.operatorNotesPlaceholder', 'Internal notes about this identity...')}
                />
                <FieldError />
              </TextField>

              <p className="text-xs text-default-400">
                {t('identities.edit.tagNote', 'Tag editing will be available in a future update.')}
              </p>

              <div className="flex items-center gap-4 pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  loadingText={t('identities.edit.submitting', 'Saving...')}
                >
                  {t('identities.edit.submit', 'Save Changes')}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onPress={() => router.visit(`/app/identities/${identity.id}/`)}
                >
                  {t('identities.edit.cancel', 'Cancel')}
                </Button>
              </div>
            </Form>
          </Card.Content>
        </Card>
      </div>
    </DashboardLayout>
  )
}
