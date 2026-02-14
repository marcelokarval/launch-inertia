import { Head, Link, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip, Button as HeroButton } from '@heroui/react'
import { Button } from '@/components/ui'
import { Bell, Check, CheckCheck, User, Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Notification, Pagination } from '@/types'
import { NOTIFICATION_TYPE_COLORS } from '@/types'

interface Props {
  notifications: Notification[]
  filter: string
  pagination: Pagination
  unread_count: number
}

export default function NotificationsIndex({ notifications, filter, pagination, unread_count }: Props) {
  const { t } = useTranslation()

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (minutes < 60) return t('notifications.timeAgo.minutes', { count: minutes })
    if (hours < 24) return t('notifications.timeAgo.hours', { count: hours })
    if (days < 7) return t('notifications.timeAgo.days', { count: days })
    return date.toLocaleDateString('pt-BR')
  }

  const markAsRead = (id: string) => {
    router.post(`/notifications/${id}/read/`, {}, {
      preserveScroll: true,
      forceFormData: true,
    })
  }

  const markAllRead = () => {
    router.post('/notifications/mark-all-read/', {}, {
      preserveScroll: true,
      forceFormData: true,
    })
  }

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
            <Button
              onPress={markAllRead}
              variant="primary"
            >
              <CheckCheck className="w-4 h-4 mr-2" />
              {t('notifications.markAllRead')}
            </Button>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6">
          <Link href="/notifications/">
            <Chip
              color={filter === 'all' ? 'accent' : 'default'}
              variant={filter === 'all' ? 'soft' : 'soft'}
              className={filter !== 'all' ? 'hover:bg-default-200 cursor-pointer' : 'cursor-pointer'}
            >
              {t('notifications.filters.all')}
            </Chip>
          </Link>
          <Link href="/notifications/?status=unread">
            <Chip
              color={filter === 'unread' ? 'accent' : 'default'}
              variant="soft"
              className={filter !== 'unread' ? 'hover:bg-default-200 cursor-pointer' : 'cursor-pointer'}
            >
              {t('notifications.filters.unread')}
            </Chip>
          </Link>
          <Link href="/notifications/?status=read">
            <Chip
              color={filter === 'read' ? 'accent' : 'default'}
              variant="soft"
              className={filter !== 'read' ? 'hover:bg-default-200 cursor-pointer' : 'cursor-pointer'}
            >
              {t('notifications.filters.read')}
            </Chip>
          </Link>
        </div>

        {/* Notifications List */}
        <Card>
          <Card.Content className="p-0">
            {notifications.length > 0 ? (
              <div className="divide-y divide-divider">
                {notifications.map((notification) => {
                  const typeColors = NOTIFICATION_TYPE_COLORS[notification.type] ?? NOTIFICATION_TYPE_COLORS.info
                  return (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-default-100 transition-colors ${
                        !notification.is_read ? 'bg-primary/5' : ''
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={`p-2 rounded-full ${
                            !notification.is_read ? typeColors.bg : 'bg-default-100'
                          }`}
                        >
                          <Bell
                            className={`w-5 h-5 ${
                              !notification.is_read ? typeColors.text : 'text-default-400'
                            }`}
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <p
                                className={`font-medium ${
                                  !notification.is_read
                                    ? 'text-foreground'
                                    : 'text-default-600'
                                }`}
                              >
                                {notification.title}
                              </p>
                              <p className="text-sm text-default-500 mt-1">
                                {notification.body}
                              </p>

                              <div className="flex items-center gap-3 mt-2">
                                {notification.actor && (
                                  <span className="flex items-center gap-1 text-xs text-default-400">
                                    <User className="w-3 h-3" />
                                    {notification.actor.name}
                                  </span>
                                )}
                                <span className="flex items-center gap-1 text-xs text-default-400">
                                  <Clock className="w-3 h-3" />
                                  {formatDate(notification.created_at)}
                                </span>
                              </div>
                            </div>

                            {!notification.is_read && (
                              <Button
                                onPress={() => markAsRead(notification.id)}
                                variant="ghost"
                                size="sm"
                                aria-label={t('notifications.markAsRead')}
                              >
                                <Check className="w-4 h-4 text-default-400" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
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
        {pagination.pages > 1 && (
          <div className="flex justify-center items-center gap-1 mt-6">
            <HeroButton
              variant="ghost"
              size="sm"
              isIconOnly
              isDisabled={pagination.page <= 1}
              onPress={() => router.get('/notifications/', {
                page: pagination.page - 1,
                ...(filter !== 'all' ? { status: filter } : {}),
              }, { preserveState: true })}
              aria-label="Previous page"
            >
              <ChevronLeft className="w-4 h-4" />
            </HeroButton>
            {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((page) => (
              <HeroButton
                key={page}
                variant={page === pagination.page ? 'primary' : 'ghost'}
                size="sm"
                className="min-w-8"
                onPress={() => router.get('/notifications/', {
                  page,
                  ...(filter !== 'all' ? { status: filter } : {}),
                }, { preserveState: true })}
              >
                {page}
              </HeroButton>
            ))}
            <HeroButton
              variant="ghost"
              size="sm"
              isIconOnly
              isDisabled={pagination.page >= pagination.pages}
              onPress={() => router.get('/notifications/', {
                page: pagination.page + 1,
                ...(filter !== 'all' ? { status: filter } : {}),
              }, { preserveState: true })}
              aria-label="Next page"
            >
              <ChevronRight className="w-4 h-4" />
            </HeroButton>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
