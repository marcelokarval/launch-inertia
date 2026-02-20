import { Head, router } from '@inertiajs/react';
import DashboardLayout from '@/layouts/DashboardLayout';
import { Card, Form, SearchField, Input, Label } from '@heroui/react';
import { Button } from '@/components/ui';
import { Plus, Search } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Pagination, IdentityListItem } from '@/types';
import { EmptyState, PaginationControls, IdentityRow } from './components';

// ============================================================================
// Types
// ============================================================================

interface Props {
  identities: IdentityListItem[];
  filters: {
    q: string;
    tag: string | null;
  };
  pagination: Pagination;
}

// ============================================================================
// Main Page
// ============================================================================

export default function IdentitiesIndex({ identities, filters, pagination }: Props) {
  const { t } = useTranslation();
  const [search, setSearch] = useState(filters.q || '');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.get('/app/identities/', { q: search }, { preserveState: true });
  };

  const handlePageChange = (page: number) => {
    router.get(
      '/app/identities/',
      { page, ...(search ? { q: search } : {}) },
      { preserveState: true },
    );
  };

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
            {t('identities.index.totalCount', { total: pagination.total, defaultValue: '{{total}} identities' })}
          </p>
        </div>
        <Button
          variant="primary"
          onPress={() => router.visit('/app/identities/create/')}
        >
          <Plus className="w-4 h-4" />
          {t('identities.index.importIdentity', 'Import Identity')}
        </Button>
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
          <Card.Content>
            <EmptyState />
          </Card.Content>
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
  );
}
