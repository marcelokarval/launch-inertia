/**
 * Overview tab — default tab in Identity Show.
 *
 * Shows: event stats, intent hints, recent activity.
 */

import { Card, Chip } from '@heroui/react'
import {
  Eye, FormInput, CheckCircle, Activity, AtSign, Phone,
  RotateCcw, MapPin, CalendarDays,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { IdentityShowData, TimelineEvent } from '@/types'

interface Props {
  identity: IdentityShowData
}

function MiniTimeline({ events }: { events: TimelineEvent[] }) {
  const { t } = useTranslation()

  if (events.length === 0) {
    return (
      <p className="text-sm text-default-400">
        {t('identities.show.overview.noActivity', 'No recent activity')}
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {events.map((event) => (
        <div key={event.id} className="flex items-center justify-between gap-2 text-sm">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-foreground capitalize truncate">
              {event.event_type.replace(/_/g, ' ')}
            </span>
            {event.page_url && (
              <span className="text-default-400 truncate text-xs">
                {event.page_url}
              </span>
            )}
          </div>
          <span className="text-xs text-default-400 whitespace-nowrap">
            {new Date(event.timestamp).toLocaleString(undefined, {
              day: '2-digit',
              month: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      ))}
    </div>
  )
}

export function OverviewTab({ identity }: Props) {
  const { t } = useTranslation()
  const stats = identity.overview_stats
  const hints = identity.intent_hints
  const hasHints = hints.email_domains.length > 0 || hints.phone_prefixes.length > 0
  const recentEvents = identity.timeline.slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Event Stats */}
      <div>
        <h4 className="text-sm font-semibold text-foreground mb-3">
          {t('identities.show.overview.activityStats', 'Activity Stats')}
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatMini
            icon={<Eye className="w-4 h-4 text-primary" />}
            label={t('identities.show.overview.pageViews', 'Page Views')}
            value={stats.page_views}
          />
          <StatMini
            icon={<FormInput className="w-4 h-4 text-accent" />}
            label={t('identities.show.overview.formIntents', 'Form Intents')}
            value={stats.form_intents}
          />
          <StatMini
            icon={<CheckCircle className="w-4 h-4 text-success" />}
            label={t('identities.show.overview.submissions', 'Submissions')}
            value={stats.form_submissions}
          />
          <StatMini
            icon={<Activity className="w-4 h-4 text-default-500" />}
            label={t('identities.show.overview.totalEvents', 'Total Events')}
            value={stats.total_events}
          />
        </div>
      </div>

      {/* Session History (P4.2) */}
      <div>
        <h4 className="text-sm font-semibold text-foreground mb-3">
          {t('identities.show.overview.sessionHistory', 'Session History')}
        </h4>
        <div className="grid grid-cols-3 gap-3">
          <StatMini
            icon={<RotateCcw className="w-4 h-4 text-primary" />}
            label={t('identities.show.overview.visitSessions', 'Sessions')}
            value={stats.visit_sessions}
          />
          <StatMini
            icon={<MapPin className="w-4 h-4 text-warning" />}
            label={t('identities.show.overview.uniquePages', 'Unique Pages')}
            value={stats.unique_pages}
          />
          <StatMini
            icon={<CalendarDays className="w-4 h-4 text-success" />}
            label={t('identities.show.overview.daysActive', 'Days Active')}
            value={stats.days_active}
          />
        </div>
      </div>

      {/* Intent Hints */}
      {hasHints && (
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-3">
            {t('identities.show.overview.knownHints', 'Known Hints')}
          </h4>
          <Card className="border border-default-200">
            <Card.Content className="p-4">
              <div className="space-y-3">
                {hints.email_domains.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <AtSign className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="text-sm text-default-500">
                      {t('identities.show.overview.emailDomains', 'Email domains')}:
                    </span>
                    {hints.email_domains.map((domain) => (
                      <Chip key={domain} size="sm" variant="soft" color="accent">
                        @{domain}
                      </Chip>
                    ))}
                  </div>
                )}
                {hints.phone_prefixes.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <Phone className="w-4 h-4 text-success flex-shrink-0" />
                    <span className="text-sm text-default-500">
                      {t('identities.show.overview.phonePrefixes', 'Phone prefixes')}:
                    </span>
                    {hints.phone_prefixes.map((prefix) => (
                      <Chip key={prefix} size="sm" variant="soft" color="success">
                        {prefix}...
                      </Chip>
                    ))}
                  </div>
                )}
              </div>
            </Card.Content>
          </Card>
        </div>
      )}

      {/* Recent Activity */}
      <div>
        <h4 className="text-sm font-semibold text-foreground mb-3">
          {t('identities.show.overview.recentActivity', 'Recent Activity')}
        </h4>
        <Card className="border border-default-200">
          <Card.Content className="p-4">
            <MiniTimeline events={recentEvents} />
          </Card.Content>
        </Card>
      </div>
    </div>
  )
}

function StatMini({ icon, label, value }: {
  icon: React.ReactNode
  label: string
  value: number
}) {
  return (
    <div className="p-3 rounded-lg bg-content2 text-center">
      <div className="flex items-center justify-center gap-1.5 mb-1">
        {icon}
        <span className="text-xl font-bold text-foreground">{value}</span>
      </div>
      <p className="text-xs text-default-500">{label}</p>
    </div>
  )
}
