import { Head, router } from '@inertiajs/react';
import DashboardLayout from '@/layouts/DashboardLayout';
import { Card, Chip } from '@heroui/react';
import { Button } from '@/components/ui';
import { Bell, CheckCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Notification, Pagination } from '@/types';
import { NotificationItem } from './components/NotificationItem';
import { NotificationPagination } from './components/NotificationPagination';

interface Props {
  notifications: Notification[];
  filter: string;
  pagination: Pagination;
  unread_count: number;
}

export default function NotificationsIndex({ notifications, filter, pagination, unread_count }: Props) {
  const { t } = useTranslation();

  const markAsRead = (id: string) => {
    router.post(`/app/notifications/${id}/read/`, {}, {
      preserveScroll: true,
      forceFormData: true,
    });
  };

  const markAllRead = () => {
    router.post('/app/notifications/mark-all-read/', {}, {
      preserveScroll: true,
      forceFormData: true,
    });
  };

  return (
    <DashboardLayout title={t('notifications.title')}>
      <Head title={t('notifications.pageTitle')} />

      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              {t('notifications.title')}
            </h2>
            <p className="text-default-500">
              {unread_count > 0
                ? t('notifications.unreadCount', { count: unread_count })
                : t('notifications.allRead')}
            </p>
          </div>

          {unread_count > 0 && (
            <Button onPress={markAllRead} variant="primary">
              <CheckCheck className="w-4 h-4 mr-2" />
              {t('notifications.markAllRead')}
            </Button>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6">
          {(['all', 'unread', 'read'] as const).map((status) => (
            <Chip
              key={status}
              color={filter === status ? 'accent' : 'default'}
              variant="soft"
              className={`cursor-pointer ${filter !== status ? 'hover:bg-default-200' : ''}`}
              onClick={() =>
                router.get('/app/notifications/', status !== 'all' ? { status } : {}, { preserveState: true })
              }
            >
              {t(`notifications.filters.${status}`)}
            </Chip>
          ))}
        </div>

        {/* Notifications List */}
        <Card>
          <Card.Content className="p-0">
            {notifications.length > 0 ? (
              <div className="divide-y divide-divider">
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={markAsRead}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Bell className="w-12 h-12 text-default-300 mx-auto mb-4" />
                <p className="text-default-500">{t('notifications.empty')}</p>
              </div>
            )}
          </Card.Content>
        </Card>

        {/* Pagination */}
        <NotificationPagination pagination={pagination} filter={filter} />
      </div>
    </DashboardLayout>
  );
}
