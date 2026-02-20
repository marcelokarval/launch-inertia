/**
 * Event timeline for the Identity detail tabs.
 */

import { Activity, Eye, Edit, ExternalLink } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { TimelineEvent } from '@/types'

function eventIcon(type: string) {
  if (type === 'page_view') return <Eye className="w-3.5 h-3.5 text-primary" />
  if (type === 'form_submit') return <Edit className="w-3.5 h-3.5 text-success" />
  if (type === 'click') return <ExternalLink className="w-3.5 h-3.5 text-warning" />
  return <Activity className="w-3.5 h-3.5 text-default-400" />
}

interface Props {
  events: TimelineEvent[]
}

export function TimelineSection({ events }: Props) {
  const { t } = useTranslation()

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.timeline.noEvents', 'No events recorded')}</p>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-[17px] top-6 bottom-6 w-px bg-default-200" />

      <div className="space-y-4">
        {events.map((event) => (
          <div key={event.id} className="flex items-start gap-3 relative">
            <div className="w-[35px] h-[35px] rounded-full bg-content2 border border-default-200 flex items-center justify-center flex-shrink-0 z-10">
              {eventIcon(event.event_type)}
            </div>
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-foreground capitalize">
                  {event.event_type.replace('_', ' ')}
                </p>
                <span className="text-xs text-default-400 whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleString(undefined, {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
              {event.page_url && (
                <p className="text-xs text-default-400 truncate mt-0.5">
                  {event.page_url}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
