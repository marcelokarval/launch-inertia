import { Head, Link } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, TextField, Input, Label, FieldError, Form, TextArea } from '@heroui/react'
import { Button } from '@/components/ui'
import { User, Mail, Phone, Building, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAppForm } from '@/hooks/useAppForm'
import type { ContactDetail } from '@/types'

interface Props {
  contact: ContactDetail
  errors?: Record<string, string>
}

export default function ContactEdit({ contact, errors = {} }: Props) {
  const { t } = useTranslation()
  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      name: contact.name || '',
      email: contact.email || '',
      phone: contact.phone || '',
      company: contact.company || '',
      job_title: contact.job_title || '',
      notes: contact.notes || '',
    },
    url: `/contacts/${contact.id}/edit/`,
    method: 'post',
  })

  return (
    <DashboardLayout title={t('contacts.edit.pageTitle', { name: contact.name })}>
      <Head title={t('contacts.edit.pageTitle', { name: contact.name })} />

      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href={`/contacts/${contact.id}/`}
            className="p-2 rounded-lg hover:bg-default-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              {t('contacts.edit.title')}
            </h2>
            <p className="text-default-500">{t('contacts.edit.description', { name: contact.name })}</p>
          </div>
        </div>

        <Card>
          <Card.Content className="p-6">
            <Form
              onSubmit={submit}
              validationErrors={errors}
              className="space-y-6"
            >
              <TextField name="name" className="space-y-2" isRequired>
                <Label>{t('contacts.create.nameLabel')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="text"
                    value={data.name}
                    onChange={(e) => setData('name', e.target.value)}
                    className="pl-10"
                    placeholder={t('contacts.create.namePlaceholder')}
                  />
                </div>
                <FieldError />
              </TextField>

              <TextField name="email" className="space-y-2">
                <Label>{t('contacts.create.emailLabel')}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="email"
                    value={data.email}
                    onChange={(e) => setData('email', e.target.value)}
                    className="pl-10"
                    placeholder={t('contacts.create.emailPlaceholder')}
                  />
                </div>
                <FieldError />
              </TextField>

              <TextField name="phone" className="space-y-2">
                <Label>{t('contacts.create.phoneLabel')}</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="tel"
                    value={data.phone}
                    onChange={(e) => setData('phone', e.target.value)}
                    className="pl-10"
                    placeholder={t('contacts.create.phonePlaceholder')}
                  />
                </div>
                <FieldError />
              </TextField>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TextField name="company" className="space-y-2">
                  <Label>{t('contacts.create.companyLabel')}</Label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                    <Input
                      type="text"
                      value={data.company}
                      onChange={(e) => setData('company', e.target.value)}
                      className="pl-10"
                      placeholder={t('contacts.create.companyPlaceholder')}
                    />
                  </div>
                  <FieldError />
                </TextField>

                <TextField name="job_title" className="space-y-2">
                  <Label>{t('contacts.create.positionLabel')}</Label>
                  <Input
                    type="text"
                    value={data.job_title}
                    onChange={(e) => setData('job_title', e.target.value)}
                    placeholder={t('contacts.create.positionPlaceholder')}
                  />
                  <FieldError />
                </TextField>
              </div>

              <TextField name="notes" className="space-y-2">
                <Label>{t('contacts.create.notesLabel')}</Label>
                <TextArea
                  value={data.notes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setData('notes', e.target.value)}
                  placeholder={t('contacts.create.notesPlaceholder')}
                />
                <FieldError />
              </TextField>

              <div className="flex items-center gap-4 pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  loadingText={t('contacts.edit.submitting')}
                  isDisabled={!data.name}
                >
                  {t('contacts.edit.submit')}
                </Button>
                <Link href={`/contacts/${contact.id}/`}>
                  <Button type="button" variant="secondary">
                    {t('contacts.edit.cancel')}
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
