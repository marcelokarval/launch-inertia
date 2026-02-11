import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip, Form, SearchField, Input, Label } from '@heroui/react'
import { Button } from '@/components/ui'
import {
  Plus, Search, Mail, Phone, Shield, Fingerprint, User,
  ChevronLeft, ChevronRight, Users,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Contact, Pagination } from '@/types'
import { CONTACT_STATUS_CHIP_COLOR, IDENTITY_STATUS_CHIP_COLOR } from '@/types'

interface Props {
  contacts: Contact[]
  filters: {
    q: string
    tag: string | null
  }
  pagination: Pagination
}

// ============================================================================
// Confidence Badge (reused from Show page, inline here for independence)
// ============================================================================

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'text-success' : pct >= 40 ? 'text-warning' : 'text-danger'
  const bg = pct >= 70 ? 'bg-success/10' : pct >= 40 ? 'bg-warning/10' : 'bg-danger/10'

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${bg}`}>
      <Shield className={`w-3 h-3 ${color}`} />
      <span className={`text-xs font-semibold ${color}`}>{pct}%</span>
    </div>
  )
}

// ============================================================================
// Channel Count Indicator
// ============================================================================

function ChannelCounts({ emailCount, phoneCount, fpCount }: {
  emailCount: number
  phoneCount: number
  fpCount: number
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex items-center gap-1 text-xs text-default-400" title="Emails">
        <Mail className="w-3 h-3" />
        <span>{emailCount}</span>
      </span>
      <span className="flex items-center gap-1 text-xs text-default-400" title="Phones">
        <Phone className="w-3 h-3" />
        <span>{phoneCount}</span>
      </span>
      <span className="flex items-center gap-1 text-xs text-default-400" title="Devices">
        <Fingerprint className="w-3 h-3" />
        <span>{fpCount}</span>
      </span>
    </div>
  )
}

// ============================================================================
// Contact Row Card
// ============================================================================

function ContactRow({ contact }: { contact: Contact }) {
  const { t } = useTranslation()
  const summary = contact.identity_summary

  return (
    <Link
      href={`/contacts/${contact.id}/`}
      className="block"
    >
      <div className="flex items-center gap-4 px-5 py-4 hover:bg-default-50 transition-colors border-b border-divider last:border-b-0">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-primary" />
        </div>

        {/* Name + contact info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-foreground truncate">
              {contact.name}
            </p>
            {summary && (
              <ConfidenceBadge score={summary.confidence_score} />
            )}
          </div>
          <div className="flex items-center gap-4 mt-0.5">
            {contact.email && (
              <span className="flex items-center gap-1 text-xs text-default-500 truncate">
                <Mail className="w-3 h-3 flex-shrink-0" />
                {contact.email}
              </span>
            )}
            {contact.phone && (
              <span className="flex items-center gap-1 text-xs text-default-500">
                <Phone className="w-3 h-3 flex-shrink-0" />
                {contact.phone}
              </span>
            )}
          </div>
        </div>

        {/* Identity channels */}
        <div className="hidden md:block flex-shrink-0">
          {summary ? (
            <div className="flex items-center gap-3">
              <Chip
                color={IDENTITY_STATUS_CHIP_COLOR[summary.status]}
                variant="soft"
                size="sm"
              >
                {summary.status}
              </Chip>
              <ChannelCounts
                emailCount={summary.email_count}
                phoneCount={summary.phone_count}
                fpCount={summary.fingerprint_count}
              />
            </div>
          ) : (
            <span className="text-xs text-default-300 italic">
              {t('contacts.index.noIdentity', 'No identity')}
            </span>
          )}
        </div>

        {/* Company */}
        <div className="hidden lg:block w-32 flex-shrink-0">
          {contact.company ? (
            <p className="text-xs text-default-500 truncate">{contact.company}</p>
          ) : (
            <span className="text-xs text-default-300">-</span>
          )}
        </div>

        {/* Status */}
        <div className="flex-shrink-0">
          <Chip
            color={CONTACT_STATUS_CHIP_COLOR[contact.status] ?? 'default'}
            variant="soft"
            size="sm"
          >
            {contact.status}
          </Chip>
        </div>

        {/* Tags */}
        <div className="hidden xl:flex gap-1 flex-shrink-0 max-w-[160px]">
          {contact.tags.slice(0, 2).map((tag) => (
            <span
              key={tag.id}
              className="px-2 py-0.5 text-[10px] rounded-full truncate"
              style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
            >
              {tag.name}
            </span>
          ))}
          {contact.tags.length > 2 && (
            <span className="text-[10px] text-default-400">
              +{contact.tags.length - 2}
            </span>
          )}
        </div>

        {/* Edit link */}
        <div className="flex-shrink-0">
          <Link
            href={`/contacts/${contact.id}/edit/`}
            className="text-xs text-primary hover:text-primary/80 font-medium"
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          >
            {t('contacts.index.table.edit', 'Edit')}
          </Link>
        </div>
      </div>
    </Link>
  )
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-full bg-default-100 flex items-center justify-center mb-4">
        <Users className="w-8 h-8 text-default-300" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-1">
        {t('contacts.index.emptyTitle', 'No contacts yet')}
      </h3>
      <p className="text-sm text-default-500 mb-4 text-center max-w-sm">
        {t('contacts.index.emptyDesc', 'Start building your audience by adding your first contact.')}
      </p>
      <Link href="/contacts/create/">
        <Button variant="primary">
          <Plus className="w-4 h-4" />
          {t('contacts.index.addFirst', 'Add your first contact')}
        </Button>
      </Link>
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

export default function ContactsIndex({ contacts, filters, pagination }: Props) {
  const { t } = useTranslation()
  const [search, setSearch] = useState(filters.q || '')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    router.get('/contacts/', { q: search }, { preserveState: true })
  }

  return (
    <DashboardLayout title={t('contacts.index.title', 'Contacts')}>
      <Head title={t('contacts.index.pageTitle', 'Contacts')} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">
            {t('contacts.index.title', 'Contacts')}
          </h2>
          <p className="text-sm text-default-500">
            {t('contacts.index.totalCount', { total: pagination.total })}
          </p>
        </div>
        <Link href="/contacts/create/">
          <Button variant="primary">
            <Plus className="w-4 h-4" />
            {t('contacts.index.addContact', 'Add Contact')}
          </Button>
        </Link>
      </div>

      {/* Search Bar */}
      <Card className="border border-default-200 mb-6">
        <Card.Content className="p-4">
          <Form onSubmit={handleSearch}>
            <SearchField
              value={search}
              onChange={setSearch}
              aria-label={t('contacts.index.searchPlaceholder', 'Search contacts...')}
              className="w-full"
            >
              <Label className="sr-only">
                {t('contacts.index.searchPlaceholder', 'Search contacts...')}
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-default-400 z-10" />
                <Input
                  placeholder={t('contacts.index.searchPlaceholder', 'Search contacts...')}
                  className="pl-10"
                />
              </div>
            </SearchField>
          </Form>
        </Card.Content>
      </Card>

      {/* Contact List */}
      <Card className="border border-default-200 overflow-hidden">
        {/* Column headers (visible on md+) */}
        <div className="hidden md:flex items-center gap-4 px-5 py-3 bg-content2 border-b border-divider text-xs font-medium text-default-500 uppercase tracking-wider">
          <div className="w-10 flex-shrink-0" /> {/* Avatar spacer */}
          <div className="flex-1">
            {t('contacts.index.table.name', 'Name')}
          </div>
          <div className="hidden md:block flex-shrink-0 w-[220px]">
            {t('contacts.index.table.identity', 'Identity')}
          </div>
          <div className="hidden lg:block w-32 flex-shrink-0">
            {t('contacts.index.table.company', 'Company')}
          </div>
          <div className="flex-shrink-0 w-[80px]">
            {t('contacts.index.table.status', 'Status')}
          </div>
          <div className="hidden xl:block flex-shrink-0 w-[160px]">
            {t('contacts.index.table.tags', 'Tags')}
          </div>
          <div className="flex-shrink-0 w-[40px]" /> {/* Edit spacer */}
        </div>

        {/* Rows */}
        {contacts.length === 0 ? (
          <EmptyState />
        ) : (
          contacts.map((contact) => (
            <ContactRow key={contact.id} contact={contact} />
          ))
        )}
      </Card>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-default-500">
            {t('contacts.index.pagination.showing', {
              from: (pagination.page - 1) * pagination.per_page + 1,
              to: Math.min(pagination.page * pagination.per_page, pagination.total),
              total: pagination.total,
            })}
          </p>
          <div className="flex gap-2">
            {pagination.page > 1 && (
              <Link
                href={`/contacts/?page=${pagination.page - 1}${search ? `&q=${search}` : ''}`}
                className="flex items-center gap-1 px-3 py-2 border border-default-300 rounded-lg text-sm hover:bg-default-100 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                {t('contacts.index.pagination.previous', 'Previous')}
              </Link>
            )}
            {pagination.page < pagination.pages && (
              <Link
                href={`/contacts/?page=${pagination.page + 1}${search ? `&q=${search}` : ''}`}
                className="flex items-center gap-1 px-3 py-2 border border-default-300 rounded-lg text-sm hover:bg-default-100 transition-colors"
              >
                {t('contacts.index.pagination.next', 'Next')}
                <ChevronRight className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
