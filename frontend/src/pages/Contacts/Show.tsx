import { Head, Link } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip } from '@heroui/react'
import { Button } from '@/components/ui'
import { User, Mail, Phone, Building, Calendar, Edit, Trash2, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ContactDetail } from '@/types'

interface Props {
  contact: ContactDetail
}

export default function ContactShow({ contact }: Props) {
  const { t } = useTranslation()

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  }

  return (
    <DashboardLayout title={contact.name}>
      <Head title={contact.name} />

      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link
              href="/contacts/"
              className="p-2 rounded-lg hover:bg-default-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-default-500" />
            </Link>
            <div>
              <h2 className="text-2xl font-bold text-foreground">
                {contact.name}
              </h2>
              {contact.job_title && contact.company && (
                <p className="text-default-500">
                  {t('contacts.show.positionAt', { position: contact.job_title, company: contact.company })}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href={`/contacts/${contact.id}/edit/`}>
              <Button variant="primary">
                <Edit className="w-4 h-4" />
                {t('contacts.show.edit')}
              </Button>
            </Link>
            <Link href={`/contacts/${contact.id}/delete/`}>
              <Button variant="danger">
                <Trash2 className="w-4 h-4" />
                {t('contacts.show.delete')}
              </Button>
            </Link>
          </div>
        </div>

        {/* Contact Info */}
        <Card>
          <Card.Content className="p-6">
            <div className="space-y-6">
              {/* Avatar & Basic Info */}
              <div className="flex items-center gap-6 pb-6 border-b border-divider">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="w-10 h-10 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground">
                    {contact.name}
                  </h3>
                  {contact.tags && contact.tags.length > 0 && (
                    <div className="flex gap-2 mt-2">
                      {contact.tags.map((tag) => (
                        <Chip
                          key={tag.id}
                          className="text-xs"
                          style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                        >
                          {tag.name}
                        </Chip>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Contact Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {contact.email && (
                  <div className="flex items-center gap-3">
                    <Mail className="w-5 h-5 text-default-400" />
                    <div>
                      <p className="text-sm text-default-500">{t('contacts.show.emailLabel')}</p>
                      <a
                        href={`mailto:${contact.email}`}
                        className="text-primary hover:text-primary-600"
                      >
                        {contact.email}
                      </a>
                    </div>
                  </div>
                )}

                {contact.phone && (
                  <div className="flex items-center gap-3">
                    <Phone className="w-5 h-5 text-default-400" />
                    <div>
                      <p className="text-sm text-default-500">{t('contacts.show.phoneLabel')}</p>
                      <a
                        href={`tel:${contact.phone}`}
                        className="text-primary hover:text-primary-600"
                      >
                        {contact.phone}
                      </a>
                    </div>
                  </div>
                )}

                {contact.company && (
                  <div className="flex items-center gap-3">
                    <Building className="w-5 h-5 text-default-400" />
                    <div>
                      <p className="text-sm text-default-500">{t('contacts.show.companyLabel')}</p>
                      <p className="text-foreground">{contact.company}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-default-400" />
                  <div>
                    <p className="text-sm text-default-500">{t('contacts.show.createdAt')}</p>
                    <p className="text-foreground">
                      {formatDate(contact.created_at)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Notes */}
              {contact.notes && (
                <div className="pt-6 border-t border-divider">
                  <h4 className="font-semibold text-foreground mb-2">
                    {t('contacts.show.notesTitle')}
                  </h4>
                  <p className="text-default-600 whitespace-pre-wrap">
                    {contact.notes}
                  </p>
                </div>
              )}
            </div>
          </Card.Content>
        </Card>
      </div>
    </DashboardLayout>
  )
}
