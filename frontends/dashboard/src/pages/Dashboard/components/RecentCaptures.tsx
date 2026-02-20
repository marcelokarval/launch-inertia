/**
 * RecentCaptures — Activity feed of latest capture submissions.
 */

import { Card, Chip } from '@heroui/react';
import { Mail, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { RecentCapture } from '@/types';

interface Props {
  captures: RecentCapture[];
}

function timeAgo(isoDate: string, t: (key: string, fallback: string, opts?: Record<string, number>) => string): string {
  const now = new Date();
  const date = new Date(isoDate);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return t('dashboard.analytics.timeAgo.now', 'now');
  if (diffMin < 60) return t('dashboard.analytics.timeAgo.minutes', '{{count}}min', { count: diffMin });
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return t('dashboard.analytics.timeAgo.hours', '{{count}}h', { count: diffHours });
  const diffDays = Math.floor(diffHours / 24);
  return t('dashboard.analytics.timeAgo.days', '{{count}}d', { count: diffDays });
}

export function RecentCaptures({ captures }: Props) {
  const { t } = useTranslation();

  if (captures.length === 0) {
    return (
      <Card className="border border-default-200 animate-fade-in">
        <Card.Header className="pb-0 px-6 pt-6">
          <h2 className="text-lg font-semibold text-foreground">
            {t('dashboard.analytics.capturasRecentes', 'Recent Captures')}
          </h2>
        </Card.Header>
        <Card.Content className="p-6">
          <div className="text-center py-6">
            <Mail className="h-8 w-8 text-default-300 mx-auto mb-2" />
            <p className="text-sm text-default-400">
              {t('dashboard.analytics.nenhumaCapturaAinda', 'No captures yet')}
            </p>
          </div>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">
            {t('dashboard.analytics.capturasRecentes', 'Recent Captures')}
          </h2>
        </Card.Header>
        <Card.Content className="p-6">
          <div className="space-y-3 max-h-[320px] overflow-y-auto">
          {captures.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between py-2 border-b border-default-100 last:border-0"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground truncate">
                    {c.email}
                  </span>
                  {c.is_duplicate && (
                    <Chip variant="soft" color="warning" size="sm">
                      {t('dashboard.analytics.duplicate', 'dup')}
                    </Chip>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-default-400">{c.page_name || c.page_slug}</span>
                  <span className="text-xs text-default-300">|</span>
                  <span className="text-xs text-default-400">{c.source}</span>
                </div>
              </div>
              <div className="flex items-center gap-1 text-xs text-default-400 flex-shrink-0 ml-2">
                <Clock className="h-3 w-3" />
                {timeAgo(c.created_at, t)}
              </div>
            </div>
          ))}
        </div>
      </Card.Content>
    </Card>
  );
}
