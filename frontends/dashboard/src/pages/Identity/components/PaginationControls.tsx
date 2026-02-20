import { Button as HeroButton } from '@heroui/react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Pagination } from '@/types';

interface PaginationControlsProps {
  pagination: Pagination;
  onPageChange: (page: number) => void;
}

export function PaginationControls({ pagination, onPageChange }: PaginationControlsProps) {
  const { t } = useTranslation();
  const pages = Array.from({ length: pagination.pages }, (_, i) => i + 1);

  const getVisiblePages = () => {
    if (pagination.pages <= 7) return pages;
    const current = pagination.page;
    const result: (number | 'ellipsis-start' | 'ellipsis-end')[] = [1];
    if (current > 3) result.push('ellipsis-start');
    const start = Math.max(2, current - 1);
    const end = Math.min(pagination.pages - 1, current + 1);
    for (let i = start; i <= end; i++) result.push(i);
    if (current < pagination.pages - 2) result.push('ellipsis-end');
    if (pagination.pages > 1) result.push(pagination.pages);
    return result;
  };

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
          aria-label={t('identities.index.pagination.previousPage', 'Previous page')}
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
          aria-label={t('identities.index.pagination.nextPage', 'Next page')}
        >
          <ChevronRight className="w-4 h-4" />
        </HeroButton>
      </div>
    </div>
  );
}
