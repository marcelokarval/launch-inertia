/**
 * NotificationPagination — Page controls for the notification list.
 */

import { router } from '@inertiajs/react';
import { Button as HeroButton } from '@heroui/react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Pagination } from '@/types';

interface Props {
  pagination: Pagination;
  filter: string;
}

export function NotificationPagination({ pagination, filter }: Props) {
  const { t } = useTranslation();

  if (pagination.pages <= 1) return null;

  const navigateTo = (page: number) => {
    router.get('/app/notifications/', {
      page,
      ...(filter !== 'all' ? { status: filter } : {}),
    }, { preserveState: true });
  };

  return (
    <div className="flex justify-center items-center gap-1 mt-6">
      <HeroButton
        variant="ghost"
        size="sm"
        isIconOnly
        isDisabled={pagination.page <= 1}
        onPress={() => navigateTo(pagination.page - 1)}
        aria-label={t('notifications.pagination.previous', 'Previous page')}
      >
        <ChevronLeft className="w-4 h-4" />
      </HeroButton>
      {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((page) => (
        <HeroButton
          key={page}
          variant={page === pagination.page ? 'primary' : 'ghost'}
          size="sm"
          className="min-w-8"
          onPress={() => navigateTo(page)}
        >
          {page}
        </HeroButton>
      ))}
      <HeroButton
        variant="ghost"
        size="sm"
        isIconOnly
        isDisabled={pagination.page >= pagination.pages}
        onPress={() => navigateTo(pagination.page + 1)}
        aria-label={t('notifications.pagination.next', 'Next page')}
      >
        <ChevronRight className="w-4 h-4" />
      </HeroButton>
    </div>
  );
}
