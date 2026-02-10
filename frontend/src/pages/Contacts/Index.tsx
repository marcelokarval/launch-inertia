import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Form, SearchField, Input, Label, Chip } from '@heroui/react'
import { Plus, Search, Mail, Phone } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Contact, Pagination } from '@/types'
import { CONTACT_STATUS_CHIP_COLOR } from '@/types'

interface Props {
  contacts: Contact[]
  filters: {
    q: string
    tag: string | null
  }
  pagination: Pagination
}

export default function ContactsIndex({ contacts, filters, pagination }: Props) {
  const { t } = useTranslation()
  const [search, setSearch] = useState(filters.q || '')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    router.get('/contacts/', { q: search }, { preserveState: true })
  }

  return (
    <DashboardLayout title={t('contacts.index.title')}>
      <Head title={t('contacts.index.pageTitle')} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">{t('contacts.index.title')}</h2>
          <p className="text-default-500">
            {t('contacts.index.totalCount', { total: pagination.total })}
          </p>
        </div>
        <Link
          href="/contacts/create/"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('contacts.index.addContact')}
        </Link>
      </div>

      {/* Search */}
      <Form onSubmit={handleSearch} className="mb-6">
        <SearchField
          value={search}
          onChange={setSearch}
          aria-label={t('contacts.index.searchPlaceholder')}
          className="w-full"
        >
          <Label className="sr-only">{t('contacts.index.searchPlaceholder')}</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-default-400 z-10" />
            <Input
              placeholder={t('contacts.index.searchPlaceholder')}
              className="pl-10"
            />
          </div>
        </SearchField>
      </Form>

      {/* Table */}
      <div className="bg-content1 rounded-lg shadow-sm border border-default-200 overflow-hidden">
        <table className="min-w-full divide-y divide-divider">
          <thead className="bg-content2">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-default-500 uppercase tracking-wider">
                {t('contacts.index.table.name')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-default-500 uppercase tracking-wider">
                {t('contacts.index.table.contact')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-default-500 uppercase tracking-wider">
                {t('contacts.index.table.company')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-default-500 uppercase tracking-wider">
                {t('contacts.index.table.status')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-default-500 uppercase tracking-wider">
                {t('contacts.index.table.tags')}
              </th>
              <th className="relative px-6 py-3">
                <span className="sr-only">{t('contacts.index.table.actions')}</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-divider">
            {contacts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-default-500">
                  {t('contacts.index.empty')}{' '}
                  <Link href="/contacts/create/" className="text-primary hover:underline">
                    {t('contacts.index.addFirst')}
                  </Link>
                </td>
              </tr>
            ) : (
              contacts.map((contact) => {
                const chipColor = CONTACT_STATUS_CHIP_COLOR[contact.status] ?? 'primary'
                return (
                  <tr key={contact.id} className="hover:bg-default-100">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/contacts/${contact.id}/`}
                        className="text-sm font-medium text-foreground hover:text-primary"
                      >
                        {contact.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        {contact.email && (
                          <span className="flex items-center gap-1 text-sm text-default-500">
                            <Mail className="w-3 h-3" />
                            {contact.email}
                          </span>
                        )}
                        {contact.phone && (
                          <span className="flex items-center gap-1 text-sm text-default-500">
                            <Phone className="w-3 h-3" />
                            {contact.phone}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-default-500">
                      {contact.company || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Chip color={chipColor} variant="soft" size="sm">
                        {contact.status}
                      </Chip>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-1">
                        {contact.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag.id}
                            className="px-2 py-0.5 text-xs rounded-full"
                            style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                          >
                            {tag.name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        href={`/contacts/${contact.id}/edit/`}
                        className="text-primary hover:text-primary/80"
                      >
                        {t('contacts.index.table.edit')}
                      </Link>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-default-500 ">
            {t('contacts.index.pagination.showing', {
              from: (pagination.page - 1) * pagination.per_page + 1,
              to: Math.min(pagination.page * pagination.per_page, pagination.total),
              total: pagination.total,
            })}
          </p>
          <div className="flex gap-2">
            {pagination.page > 1 && (
              <Link
                href={`/contacts/?page=${pagination.page - 1}`}
                className="px-4 py-2 border border-default-300 rounded-lg text-sm hover:bg-default-100"
              >
                {t('contacts.index.pagination.previous')}
              </Link>
            )}
            {pagination.page < pagination.pages && (
              <Link
                href={`/contacts/?page=${pagination.page + 1}`}
                className="px-4 py-2 border border-default-300 rounded-lg text-sm hover:bg-default-100"
              >
                {t('contacts.index.pagination.next')}
              </Link>
            )}
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
