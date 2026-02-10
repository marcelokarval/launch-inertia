import { Head, Link } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Form } from '@heroui/react'
import { Button } from '@/components/ui'
import { AlertTriangle, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAppForm } from '@/hooks/useAppForm'
import type { Contact } from '@/types'

interface Props {
  contact: Pick<Contact, 'id' | 'name' | 'email'>
}

export default function ContactDelete({ contact }: Props) {
  const { t } = useTranslation()
  const { submit, isSubmitting } = useAppForm({
    initialData: {},
    url: `/contacts/${contact.id}/delete/`,
    method: 'post',
  })

  return (
    <DashboardLayout title={t('contacts.delete.pageTitle', { name: contact.name })}>
      <Head title={t('contacts.delete.pageTitle', { name: contact.name })} />

      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href={`/contacts/${contact.id}/`}
            className="p-2 rounded-lg hover:bg-default-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Link>
          <h2 className="text-2xl font-bold text-foreground">
            {t('contacts.delete.title')}
          </h2>
        </div>

        <Card>
          <Card.Content className="p-6 text-center">
            <div className="w-16 h-16 bg-danger/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-10 h-10 text-danger" />
            </div>

            <h3 className="text-xl font-semibold text-foreground mb-2">
              {t('contacts.delete.confirm')}
            </h3>

            <p className="text-default-500 mb-2">
              {t('contacts.delete.warning')}
            </p>

            <p className="font-semibold text-foreground text-lg mb-1">
              {contact.name}
            </p>
            {contact.email && (
              <p className="text-default-500 text-sm mb-6">{contact.email}</p>
            )}

            <p className="text-sm text-default-500 mb-8">
              {t('contacts.delete.reversible')}
            </p>

            <Form onSubmit={submit} className="flex items-center justify-center gap-4">
              <Link href={`/contacts/${contact.id}/`}>
                <Button type="button" variant="secondary">
                  {t('contacts.delete.cancel')}
                </Button>
              </Link>
              <Button
                type="submit"
                variant="danger"
                isLoading={isSubmitting}
                loadingText={t('contacts.delete.submitting')}
              >
                {t('contacts.delete.submit')}
              </Button>
            </Form>
          </Card.Content>
        </Card>
      </div>
    </DashboardLayout>
  )
}
