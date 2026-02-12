import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip, Form, SearchField, Input, Label } from '@heroui/react'
import { Button } from '@/components/ui'
import {
  Plus, Search, Mail, Phone, Shield, Fingerprint, User,
  ChevronLeft, ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Pagination, Tag } from '@/types'
import { IDENTITY_STATUS_CHIP_COLOR } from '@/types'

// ============================================================================
// Types
// ============================================================================

interface IdentityListItem {
  id: string
  display_name: string
  status: 'active' | 'merged' | 'inactive'
  confidence_score: number
  primary_email: string | null
  primary_phone: string | null
  email_count: number
  phone_count: number
  fingerprint_count: number
  tags: Tag[]
  lifecycle_global: Record<string, unknown>
  last_seen: string | null
  created_at: string | null
}

interface Props {
  identities: IdentityListItem[]
  filters: {
    q: string
    tag: string | null
  }
  pagination: Pagination
}

// ============================================================================
// Confidence Badge
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
// Identity Row Card
// ============================================================================

function IdentityRow({ identity }: { identity: IdentityListItem }) {
  const { t } = useTranslation('identities')

  return (
    <Link
      href={`/identities/${identity.id}/`}
      className="block"
    >
      <div className="flex items-center gap-4 px-5 py-4 hover:bg-default-50 transition-colors border-b border-divider last:border-b-0">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-primary" />
        </div>

        {/* Name + primary contact */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-foreground truncate">
              {identity.display_name || t('index.anonymous', 'Anonymous')}
            </p>
            <ConfidenceBadge score={identity.confidence_score} />
          </div>
          <div className="flex items-center gap-4 mt-0.5">
            {identity.primary_email && (
              <span className="flex items-center gap-1 text-xs text-default-500 truncate">
                <Mail className="w-3 h-3 flex-shrink-0" />
                {identity.primary_email}
              </span>
            )}
            {identity.primary_phone && (
              <span className="flex items-center gap-1 text-xs text-default-500">
                <Phone className="w-3 h-3 flex-shrink-0" />
                {identity.primary_phone}
              </span>
            )}
          </div>
        </div>

        {/* Channels */}
        <div className="hidden md:flex items-center gap-3 flex-shrink-0">
          <ChannelCounts
            emailCount={identity.email_count}
            phoneCount={identity.phone_count}
            fpCount={identity.fingerprint_count}
          />
        </div>

        {/* Tags */}
        <div className="hidden xl:flex gap-1 flex-shrink-0 max-w-[160px]">
          {identity.tags.slice(0, 2).map((tag) => (
            <span
              key={tag.id}
              className="px-2 py-0.5 text-[10px] rounded-full truncate"
              style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
            >
              {tag.name}
            </span>
          ))}
          {identity.tags.length > 2 && (
            <span className="text-[10px] text-default-400">
              +{identity.tags.length - 2}
            </span>
          )}
        </div>

        {/* Status */}
        <div className="flex-shrink-0">
          <Chip
            color={IDENTITY_STATUS_CHIP_COLOR[identity.status] ?? 'default'}
            variant="soft"
            size="sm"
          >
            {identity.status}
          </Chip>
        </div>

        {/* Last seen */}
        <div className="hidden lg:block w-24 flex-shrink-0 text-right">
          {identity.last_seen ? (
            <span className="text-xs text-default-400">
              {new Date(identity.last_seen).toLocaleDateString('pt-BR')}
            </span>
          ) : (
            <span className="text-xs text-default-300">-</span>
          )}
        </div>
      </div>
    </Link>
  )
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  const { t } = useTranslation('identities')

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-full bg-default-100 flex items-center justify-center mb-4">
        <Shield className="w-8 h-8 text-default-300" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-1">
        {t('index.emptyTitle', 'No identities yet')}
      </h3>
      <p className="text-sm text-default-500 mb-4 text-center max-w-sm">
        {t('index.emptyDesc', 'Start by importing your first identity to begin resolution.')}
      </p>
      <Link href="/identities/create/">
        <Button variant="primary">
          <Plus className="w-4 h-4" />
          {t('index.addFirst', 'Import your first identity')}
        </Button>
      </Link>
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

export default function IdentitiesIndex({ identities, filters, pagination }: Props) {
  const { t } = useTranslation('identities')
  const [search, setSearch] = useState(filters.q || '')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    router.get('/identities/', { q: search }, { preserveState: true })
  }

  return (
    <DashboardLayout title={t('index.title', 'Identities')}>
      <Head title={t('index.pageTitle', 'Identities')} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">
            {t('index.title', 'Identities')}
          </h2>
          <p className="text-sm text-default-500">
            {t('index.totalCount', { count: pagination.total, defaultValue: '{{count}} identities' })}
          </p>
        </div>
        <Link href="/identities/create/">
          <Button variant="primary">
            <Plus className="w-4 h-4" />
            {t('index.importIdentity', 'Import Identity')}
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
              aria-label={t('index.searchPlaceholder', 'Search identities...')}
              className="w-full"
            >
              <Label className="sr-only">
                {t('index.searchPlaceholder', 'Search identities...')}
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-default-400 z-10" />
                <Input
                  placeholder={t('index.searchPlaceholder', 'Search identities...')}
                  className="pl-10"
                />
              </div>
            </SearchField>
          </Form>
        </Card.Content>
      </Card>

      {/* Identity List */}
      <Card className="border border-default-200 overflow-hidden">
        {/* Column headers */}
        <div className="hidden md:flex items-center gap-4 px-5 py-3 bg-content2 border-b border-divider text-xs font-medium text-default-500 uppercase tracking-wider">
          <div className="w-10 flex-shrink-0" /> {/* Avatar spacer */}
          <div className="flex-1">
            {t('index.table.displayName', 'Display Name')}
          </div>
          <div className="hidden md:block flex-shrink-0 w-[180px]">
            {t('index.table.channels', 'Channels')}
          </div>
          <div className="hidden xl:block flex-shrink-0 w-[160px]">
            {t('index.table.tags', 'Tags')}
          </div>
          <div className="flex-shrink-0 w-[80px]">
            {t('index.table.status', 'Status')}
          </div>
          <div className="hidden lg:block w-24 flex-shrink-0 text-right">
            {t('index.table.lastSeen', 'Last Seen')}
          </div>
        </div>

        {/* Rows */}
        {identities.length === 0 ? (
          <EmptyState />
        ) : (
          identities.map((identity) => (
            <IdentityRow key={identity.id} identity={identity} />
          ))
        )}
      </Card>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-default-500">
            {t('index.pagination.showing', {
              from: (pagination.page - 1) * pagination.per_page + 1,
              to: Math.min(pagination.page * pagination.per_page, pagination.total),
              total: pagination.total,
              defaultValue: 'Showing {{from}}-{{to}} of {{total}}',
            })}
          </p>
          <div className="flex gap-2">
            {pagination.page > 1 && (
              <Link
                href={`/identities/?page=${pagination.page - 1}${search ? `&q=${search}` : ''}`}
                className="flex items-center gap-1 px-3 py-2 border border-default-300 rounded-lg text-sm hover:bg-default-100 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                {t('index.pagination.previous', 'Previous')}
              </Link>
            )}
            {pagination.page < pagination.pages && (
              <Link
                href={`/identities/?page=${pagination.page + 1}${search ? `&q=${search}` : ''}`}
                className="flex items-center gap-1 px-3 py-2 border border-default-300 rounded-lg text-sm hover:bg-default-100 transition-colors"
              >
                {t('index.pagination.next', 'Next')}
                <ChevronRight className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
