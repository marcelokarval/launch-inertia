/**
 * NotificationItem — Single notification row with read/unread styling.
 */

import { Bell, User, Clock, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui';
import type { Notification } from '@/types';
import { NOTIFICATION_TYPE_COLORS } from '@/types';

interface Props {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
}

function formatDate(dateStr: string, t: (key: string, options?: Record<string, unknown>) => string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (minutes < 60) return t('notifications.timeAgo.minutes', { count: minutes });
  if (hours < 24) return t('notifications.timeAgo.hours', { count: hours });
  if (days < 7) return t('notifications.timeAgo.days', { count: days });
  return date.toLocaleDateString();
}

export function NotificationItem({ notification, onMarkAsRead }: Props) {
  const { t } = useTranslation();
  const typeColors = NOTIFICATION_TYPE_COLORS[notification.type] ?? NOTIFICATION_TYPE_COLORS.info;

  return (
    <div
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
                  {formatDate(notification.created_at, t)}
                </span>
              </div>
            </div>

            {!notification.is_read && (
              <Button
                onPress={() => onMarkAsRead(notification.id)}
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
  );
}
