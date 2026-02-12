import { Head, Link } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Form } from '@heroui/react'
import { Button } from '@/components/ui'
import { AlertTriangle, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  identity: {
    id: string
    display_name: string
    primary_email?: string
  }
}

export default function IdentityDelete({ identity }: Props) {
  const { t } = useTranslation()
  const { submit, isSubmitting } = useAppForm({
    initialData: {},
    url: `/identities/${identity.id}/delete/`,
    method: 'post',
  })

  return (
    <DashboardLayout title={t('identities.delete.pageTitle', { name: identity.display_name || identity.id, defaultValue: 'Delete {{name}}' })}>
      <Head title={t('identities.delete.pageTitle', { name: identity.display_name || identity.id, defaultValue: 'Delete {{name}}' })} />

      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href={`/identities/${identity.id}/`}
            className="p-2 rounded-lg hover:bg-default-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Link>
          <h2 className="text-2xl font-bold text-foreground">
            {t('identities.delete.title', 'Delete Identity')}
          </h2>
        </div>

        <Card>
          <Card.Content className="p-6 text-center">
            <div className="w-16 h-16 bg-danger/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-10 h-10 text-danger" />
            </div>

            <h3 className="text-xl font-semibold text-foreground mb-2">
              {t('identities.delete.confirm', 'Are you sure you want to delete this identity?')}
            </h3>

            <p className="text-default-500 mb-2">
              {t('identities.delete.warning', 'This action will remove the identity and all associated channel data.')}
            </p>

            <p className="font-semibold text-foreground text-lg mb-1">
              {identity.display_name || identity.id}
            </p>
            {identity.primary_email && (
              <p className="text-default-500 text-sm mb-6">{identity.primary_email}</p>
            )}

            <p className="text-sm text-default-500 mb-8">
              {t('identities.delete.reversible', 'This identity uses soft-delete and can be restored by an administrator if needed.')}
            </p>

            <Form onSubmit={submit} className="flex items-center justify-center gap-4">
              <Link href={`/identities/${identity.id}/`}>
                <Button type="button" variant="secondary">
                  {t('identities.delete.cancel', 'Cancel')}
                </Button>
              </Link>
              <Button
                type="submit"
                variant="danger"
                isLoading={isSubmitting}
                loadingText={t('identities.delete.submitting', 'Deleting...')}
              >
                {t('identities.delete.submit', 'Delete Identity')}
              </Button>
            </Form>
          </Card.Content>
        </Card>
      </div>
    </DashboardLayout>
  )
}
