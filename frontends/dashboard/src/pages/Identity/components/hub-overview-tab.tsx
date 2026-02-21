import { Card } from '@heroui/react';
import { Users, Mail, Phone, Monitor, Activity, TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { HubOverviewData, IdentityHubCounts } from '@/types';

interface Props {
  overview: HubOverviewData;
  counts: IdentityHubCounts;
}

export function HubOverviewTab({ overview, counts }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5 text-primary" />}
          label={t('identities.hub.people', 'People')}
          value={counts.people}
          detail={t('identities.hub.identified', '{{count}} identified', { count: overview.identified_count })}
        />
        <StatCard
          icon={<Mail className="w-5 h-5 text-success" />}
          label={t('identities.hub.emailChannels', 'Emails')}
          value={counts.emails}
          detail={t('identities.hub.domainHints', '{{count}} domain hints', { count: overview.domain_hints.length })}
        />
        <StatCard
          icon={<Phone className="w-5 h-5 text-warning" />}
          label={t('identities.hub.phoneChannels', 'Phones')}
          value={counts.phones}
          detail={t('identities.hub.prefixHints', '{{count}} prefix hints', { count: overview.prefix_hints.length })}
        />
        <StatCard
          icon={<Monitor className="w-5 h-5 text-secondary" />}
          label={t('identities.hub.devices', 'Devices')}
          value={counts.devices}
          detail={t('identities.hub.totalEvents', '{{count}} events', { count: overview.total_events })}
        />
      </div>

      {/* Recent Activity + Attribution Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card className="border border-default-200">
          <Card.Header className="px-4 py-3 border-b border-divider">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-default-500" />
              <span className="text-sm font-semibold">{t('identities.hub.recentActivity', 'Recent Activity')}</span>
            </div>
          </Card.Header>
          <Card.Content className="p-0">
            {overview.recent_events.length === 0 ? (
              <p className="p-4 text-sm text-default-400">{t('identities.hub.noActivity', 'No activity yet')}</p>
            ) : (
              <ul className="divide-y divide-divider">
                {overview.recent_events.slice(0, 10).map((evt) => (
                  <li key={evt.id} className="px-4 py-2.5 flex items-center justify-between">
                    <div className="min-w-0">
                      <span className="text-xs font-mono text-default-500">{evt.event_type}</span>
                      <p className="text-sm text-foreground truncate">{evt.page_path}</p>
                      {evt.identity_name && (
                        <span className="text-xs text-default-400">{evt.identity_name}</span>
                      )}
                    </div>
                    {evt.created_at && (
                      <span className="text-xs text-default-400 flex-shrink-0 ml-2">
                        {formatTimeAgo(evt.created_at)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card.Content>
        </Card>

        {/* Attribution Sources */}
        <Card className="border border-default-200">
          <Card.Header className="px-4 py-3 border-b border-divider">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-default-500" />
              <span className="text-sm font-semibold">{t('identities.hub.attributionSources', 'Attribution Sources')}</span>
            </div>
          </Card.Header>
          <Card.Content className="p-0">
            {overview.attribution_sources.length === 0 ? (
              <p className="p-4 text-sm text-default-400">{t('identities.hub.noSources', 'No attribution data yet')}</p>
            ) : (
              <table className="w-full">
                <tbody>
                  {overview.attribution_sources.map((src) => (
                    <tr key={src.source} className="border-b border-divider last:border-0">
                      <td className="px-4 py-2.5 text-sm text-foreground">{src.source}</td>
                      <td className="px-4 py-2.5 text-sm text-default-500 text-right">{src.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card.Content>
        </Card>
      </div>

      {/* Tags */}
      <Card className="border border-default-200">
        <Card.Header className="px-4 py-3 border-b border-divider">
          <span className="text-sm font-semibold">{t('identities.hub.tags', 'Tags')}</span>
        </Card.Header>
        <Card.Content className="p-4">
          {overview.tags.length === 0 ? (
            <p className="text-sm text-default-400">{t('identities.hub.noTags', 'No tags created yet')}</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {overview.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border border-default-200 bg-default-50"
                >
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tag.color }} />
                  {tag.name}
                  <span className="text-default-400">({tag.identity_count})</span>
                </span>
              ))}
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}

function StatCard({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: number; detail: string }) {
  return (
    <Card className="border border-default-200">
      <Card.Content className="p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-default-100">{icon}</div>
          <div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            <p className="text-sm text-default-500">{label}</p>
            <p className="text-xs text-default-400">{detail}</p>
          </div>
        </div>
      </Card.Content>
    </Card>
  );
}

function formatTimeAgo(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}
