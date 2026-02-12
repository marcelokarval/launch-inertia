import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import {
  Card, Chip, Form, SearchField, Input, Label,
  Table, Pagination, Tooltip, Avatar,
} from '@heroui/react'
import { Button } from '@/components/ui'
import {
  Plus, Search, Mail, Phone, Shield, Fingerprint, User,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Pagination as PaginationType, Tag } from '@/types'
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
  pagination: PaginationType
}

// ============================================================================
// Confidence Badge (HeroUI Chip)
// ============================================================================

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger'

  return (
    <Chip
      color={color}
      variant="soft"
      size="sm"
      startContent={<Shield className="w-3 h-3" />}
    >
      {pct}%
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
      <Tooltip content="Emails">
        <span className="flex items-center gap-1 text-xs text-default-400">
          <Mail className="w-3 h-3" />
          <span>{emailCount}</span>
        </span>
      </Tooltip>
      <Tooltip content="Phones">
        <span className="flex items-center gap-1 text-xs text-default-400">
          <Phone className="w-3 h-3" />
          <span>{phoneCount}</span>
        </span>
      </Tooltip>
      <Tooltip content="Devices">
        <span className="flex items-center gap-1 text-xs text-default-400">
          <Fingerprint className="w-3 h-3" />
          <span>{fpCount}</span>
        </span>
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
          classNames={{
            base: 'max-w-[75px]',
            content: 'truncate text-[10px]',
          }}
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
      <Avatar
        fallback={<Shield className="w-8 h-8 text-default-300" />}
        size="lg"
        className="mb-4 bg-default-100"
      />
      <h3 className="text-lg font-semibold text-foreground mb-1">
        {t('identities.index.emptyTitle', 'No identities yet')}
      </h3>
      <p className="text-sm text-default-500 mb-4 text-center max-w-sm">
        {t('identities.index.emptyDesc', 'Start by importing your first identity to begin resolution.')}
      </p>
      <Link href="/identities/create/">
        <Button variant="primary">
          <Plus className="w-4 h-4" />
          {t('identities.index.addFirst', 'Import your first identity')}
        </Button>
      </Link>
    </div>
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
    router.get('/identities/', { q: search }, { preserveState: true })
  }

  const handlePageChange = (page: number) => {
    router.get(
      '/identities/',
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
        <Link href="/identities/create/">
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
        <Table
          aria-label={t('identities.index.title', 'Identities')}
          selectionMode="none"
          onRowAction={(key) => router.visit(`/identities/${key}/`)}
          classNames={{
            wrapper: 'border border-default-200 shadow-none',
            tr: 'cursor-pointer hover:bg-default-50 transition-colors',
          }}
        >
          <Table.Header>
            <Table.Column key="name" isRowHeader>
              {t('identities.index.table.displayName', 'Display Name')}
            </Table.Column>
            <Table.Column key="channels" className="hidden md:table-cell">
              {t('identities.index.table.channels', 'Channels')}
            </Table.Column>
            <Table.Column key="tags" className="hidden xl:table-cell">
              {t('identities.index.table.tags', 'Tags')}
            </Table.Column>
            <Table.Column key="status">
              {t('identities.index.table.status', 'Status')}
            </Table.Column>
            <Table.Column key="lastSeen" className="hidden lg:table-cell text-right">
              {t('identities.index.table.lastSeen', 'Last Seen')}
            </Table.Column>
          </Table.Header>
          <Table.Body items={identities}>
            {(identity) => (
              <Table.Row key={identity.id} id={identity.id}>
                <Table.Cell>
                  <div className="flex items-center gap-3">
                    <Avatar
                      fallback={<User className="w-4 h-4 text-primary" />}
                      size="sm"
                      className="bg-primary/10 flex-shrink-0"
                    />
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
                </Table.Cell>
                <Table.Cell className="hidden md:table-cell">
                  <ChannelCounts
                    emailCount={identity.email_count}
                    phoneCount={identity.phone_count}
                    fpCount={identity.fingerprint_count}
                  />
                </Table.Cell>
                <Table.Cell className="hidden xl:table-cell">
                  <TagChips tags={identity.tags} />
                </Table.Cell>
                <Table.Cell>
                  <Chip
                    color={IDENTITY_STATUS_CHIP_COLOR[identity.status] ?? 'default'}
                    variant="soft"
                    size="sm"
                  >
                    {identity.status}
                  </Chip>
                </Table.Cell>
                <Table.Cell className="hidden lg:table-cell text-right">
                  {identity.last_seen ? (
                    <span className="text-xs text-default-400">
                      {new Date(identity.last_seen).toLocaleDateString('pt-BR')}
                    </span>
                  ) : (
                    <span className="text-xs text-default-300">-</span>
                  )}
                </Table.Cell>
              </Table.Row>
            )}
          </Table.Body>
        </Table>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-default-500">
            {t('identities.index.pagination.showing', {
              from: (pagination.page - 1) * pagination.per_page + 1,
              to: Math.min(pagination.page * pagination.per_page, pagination.total),
              total: pagination.total,
              defaultValue: 'Showing {{from}}-{{to}} of {{total}}',
            })}
          </p>
          <Pagination
            total={pagination.pages}
            page={pagination.page}
            onChange={handlePageChange}
            showControls
            size="sm"
            variant="soft"
          />
        </div>
      )}
    </DashboardLayout>
  )
}
