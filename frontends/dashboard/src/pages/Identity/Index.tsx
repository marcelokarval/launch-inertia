import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import {
  Card, Chip, Form, SearchField, Input, Label,
  Tooltip, Avatar, Button as HeroButton,
} from '@heroui/react'
import { Button } from '@/components/ui'
import {
  Plus, Search, Mail, Phone, Shield, Fingerprint, User,
  ChevronLeft, ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Pagination as PaginationType, Tag, IdentityStatus } from '@/types'
import { IDENTITY_STATUS_CHIP_COLOR } from '@/types'

// ============================================================================
// Types
// ============================================================================

interface IdentityListItem {
  id: string
  display_name: string
  status: IdentityStatus
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
  pagination: PaginationType
}

// ============================================================================
// Confidence Badge (HeroUI Chip)
// ============================================================================

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color: 'success' | 'warning' | 'danger' = pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger'

  return (
    <Chip color={color} variant="soft" size="sm">
      <span className="inline-flex items-center gap-1">
        <Shield className="w-3 h-3" />
        {pct}%
      </span>
    </Chip>
  )
}

// ============================================================================
// Channel Count Indicator (with HeroUI Tooltip)
// ============================================================================

function ChannelCounts({ emailCount, phoneCount, fpCount }: {
  emailCount: number
  phoneCount: number
  fpCount: number
}) {
  return (
    <div className="flex items-center gap-3">
      <Tooltip>
        <Tooltip.Trigger>
          <span className="flex items-center gap-1 text-xs text-default-400">
            <Mail className="w-3 h-3" />
            <span>{emailCount}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Content>Emails</Tooltip.Content>
      </Tooltip>
      <Tooltip>
        <Tooltip.Trigger>
          <span className="flex items-center gap-1 text-xs text-default-400">
            <Phone className="w-3 h-3" />
            <span>{phoneCount}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Content>Phones</Tooltip.Content>
      </Tooltip>
      <Tooltip>
        <Tooltip.Trigger>
          <span className="flex items-center gap-1 text-xs text-default-400">
            <Fingerprint className="w-3 h-3" />
            <span>{fpCount}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Content>Devices</Tooltip.Content>
      </Tooltip>
    </div>
  )
}

// ============================================================================
// Tag Chips
// ============================================================================

function TagChips({ tags }: { tags: Tag[] }) {
  if (tags.length === 0) return null

  return (
    <div className="flex gap-1 max-w-[160px]">
      {tags.slice(0, 2).map((tag) => (
        <Chip
          key={tag.id}
          size="sm"
          variant="soft"
          className="max-w-[75px] truncate text-[10px]"
          style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
        >
          {tag.name}
        </Chip>
      ))}
      {tags.length > 2 && (
        <Chip size="sm" variant="soft" color="default">
          +{tags.length - 2}
        </Chip>
      )}
    </div>
  )
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Avatar size="lg" className="mb-4 bg-default-100">
        <Avatar.Fallback>
          <Shield className="w-8 h-8 text-default-300" />
        </Avatar.Fallback>
      </Avatar>
      <h3 className="text-lg font-semibold text-foreground mb-1">
        {t('identities.index.emptyTitle', 'No identities yet')}
      </h3>
      <p className="text-sm text-default-500 mb-4 text-center max-w-sm">
        {t('identities.index.emptyDesc', 'Start by importing your first identity to begin resolution.')}
      </p>
      <Link href="/app/identities/create/">
        <Button variant="primary">
          <Plus className="w-4 h-4" />
          {t('identities.index.addFirst', 'Import your first identity')}
        </Button>
      </Link>
    </div>
  )
}

// ============================================================================
// Pagination
// ============================================================================

function PaginationControls({ pagination, onPageChange }: {
  pagination: PaginationType
  onPageChange: (page: number) => void
}) {
  const { t } = useTranslation()
  const pages = Array.from({ length: pagination.pages }, (_, i) => i + 1)

  // Show max 7 page buttons with ellipsis
  const getVisiblePages = () => {
    if (pagination.pages <= 7) return pages
    const current = pagination.page
    const result: (number | 'ellipsis-start' | 'ellipsis-end')[] = [1]
    if (current > 3) result.push('ellipsis-start')
    const start = Math.max(2, current - 1)
    const end = Math.min(pagination.pages - 1, current + 1)
    for (let i = start; i <= end; i++) result.push(i)
    if (current < pagination.pages - 2) result.push('ellipsis-end')
    if (pagination.pages > 1) result.push(pagination.pages)
    return result
  }

  return (
    <div className="mt-6 flex items-center justify-between">
      <p className="text-sm text-default-500">
        {t('identities.index.pagination.showing', {
          from: (pagination.page - 1) * pagination.per_page + 1,
          to: Math.min(pagination.page * pagination.per_page, pagination.total),
          total: pagination.total,
          defaultValue: 'Showing {{from}}-{{to}} of {{total}}',
        })}
      </p>
      <div className="flex items-center gap-1">
        <HeroButton
          variant="ghost"
          size="sm"
          isIconOnly
          isDisabled={pagination.page <= 1}
          onPress={() => onPageChange(pagination.page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </HeroButton>
        {getVisiblePages().map((p, idx) =>
          typeof p === 'string' ? (
            <span key={p} className="px-2 text-default-400">...</span>
          ) : (
            <HeroButton
              key={idx}
              variant={p === pagination.page ? 'primary' : 'ghost'}
              size="sm"
              onPress={() => onPageChange(p)}
              className="min-w-8"
            >
              {p}
            </HeroButton>
          ),
        )}
        <HeroButton
          variant="ghost"
          size="sm"
          isIconOnly
          isDisabled={pagination.page >= pagination.pages}
          onPress={() => onPageChange(pagination.page + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </HeroButton>
      </div>
    </div>
  )
}

// ============================================================================
// Identity Row
// ============================================================================

function IdentityRow({ identity }: { identity: IdentityListItem }) {
  const { t } = useTranslation()

  return (
    <tr
      className="cursor-pointer hover:bg-default-50 transition-colors border-b border-divider last:border-b-0"
      onClick={() => router.visit(`/app/identities/${identity.id}/`)}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') router.visit(`/app/identities/${identity.id}/`) }}
    >
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <Avatar size="sm" className="bg-primary/10 flex-shrink-0">
            <Avatar.Fallback>
              <User className="w-4 h-4 text-primary" />
            </Avatar.Fallback>
          </Avatar>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-foreground truncate">
                {identity.display_name || t('identities.index.anonymous', 'Anonymous')}
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
        </div>
      </td>
      <td className="py-3 px-4 hidden md:table-cell">
        <ChannelCounts
          emailCount={identity.email_count}
          phoneCount={identity.phone_count}
          fpCount={identity.fingerprint_count}
        />
      </td>
      <td className="py-3 px-4 hidden xl:table-cell">
        <TagChips tags={identity.tags} />
      </td>
      <td className="py-3 px-4">
        <Chip
          color={IDENTITY_STATUS_CHIP_COLOR[identity.status] ?? 'default'}
          variant="soft"
          size="sm"
        >
          {identity.status}
        </Chip>
      </td>
      <td className="py-3 px-4 hidden lg:table-cell text-right">
        {identity.last_seen ? (
          <span className="text-xs text-default-400">
            {new Date(identity.last_seen).toLocaleDateString('pt-BR')}
          </span>
        ) : (
          <span className="text-xs text-default-300">-</span>
        )}
      </td>
    </tr>
  )
}

// ============================================================================
// Main Page
// ============================================================================

export default function IdentitiesIndex({ identities, filters, pagination }: Props) {
  const { t } = useTranslation()
  const [search, setSearch] = useState(filters.q || '')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    router.get('/app/identities/', { q: search }, { preserveState: true })
  }

  const handlePageChange = (page: number) => {
    router.get(
      '/app/identities/',
      { page, ...(search ? { q: search } : {}) },
      { preserveState: true },
    )
  }

  return (
    <DashboardLayout title={t('identities.index.title', 'Identities')}>
      <Head title={t('identities.index.pageTitle', 'Identities')} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">
            {t('identities.index.title', 'Identities')}
          </h2>
          <p className="text-sm text-default-500">
            {t('identities.index.totalCount', { count: pagination.total, defaultValue: '{{count}} identities' })}
          </p>
        </div>
        <Link href="/app/identities/create/">
          <Button variant="primary">
            <Plus className="w-4 h-4" />
            {t('identities.index.importIdentity', 'Import Identity')}
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
              aria-label={t('identities.index.searchPlaceholder', 'Search identities...')}
              className="w-full"
            >
              <Label className="sr-only">
                {t('identities.index.searchPlaceholder', 'Search identities...')}
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-default-400 z-10" />
                <Input
                  placeholder={t('identities.index.searchPlaceholder', 'Search identities...')}
                  className="pl-10"
                />
              </div>
            </SearchField>
          </Form>
        </Card.Content>
      </Card>

      {/* Identity Table */}
      {identities.length === 0 ? (
        <Card className="border border-default-200">
          <EmptyState />
        </Card>
      ) : (
        <Card className="border border-default-200 overflow-hidden">
          <table className="w-full" role="grid" aria-label={t('identities.index.title', 'Identities')}>
            <thead>
              <tr className="border-b border-divider bg-default-50">
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase tracking-wider">
                  {t('identities.index.table.displayName', 'Display Name')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase tracking-wider hidden md:table-cell">
                  {t('identities.index.table.channels', 'Channels')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase tracking-wider hidden xl:table-cell">
                  {t('identities.index.table.tags', 'Tags')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase tracking-wider">
                  {t('identities.index.table.status', 'Status')}
                </th>
                <th className="py-3 px-4 text-right text-xs font-semibold text-default-500 uppercase tracking-wider hidden lg:table-cell">
                  {t('identities.index.table.lastSeen', 'Last Seen')}
                </th>
              </tr>
            </thead>
            <tbody>
              {identities.map((identity) => (
                <IdentityRow key={identity.id} identity={identity} />
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <PaginationControls pagination={pagination} onPageChange={handlePageChange} />
      )}
    </DashboardLayout>
  )
}
