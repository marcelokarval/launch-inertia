/**
 * Event timeline for the Identity detail tabs.
 *
 * Displays a unified timeline merging FingerprintEvents and CaptureEvents.
 */

import { Chip } from '@heroui/react'
import {
  Activity, Eye, Edit, MousePointerClick,
  AlertTriangle, FormInput, ScrollText,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { TimelineEvent } from '@/types'

function eventIcon(type: string) {
  if (type === 'page_view') return <Eye className="w-3.5 h-3.5 text-primary" />
  if (type === 'form_submit' || type === 'form_success')
    return <Edit className="w-3.5 h-3.5 text-success" />
  if (type === 'form_intent')
    return <FormInput className="w-3.5 h-3.5 text-accent" />
  if (type === 'form_attempt')
    return <FormInput className="w-3.5 h-3.5 text-warning" />
  if (type === 'form_error')
    return <AlertTriangle className="w-3.5 h-3.5 text-danger" />
  if (type === 'click' || type === 'cta_click')
    return <MousePointerClick className="w-3.5 h-3.5 text-warning" />
  if (type === 'scroll_milestone')
    return <ScrollText className="w-3.5 h-3.5 text-default-500" />
  return <Activity className="w-3.5 h-3.5 text-default-400" />
}

function eventLabel(type: string): string {
  return type.replace(/_/g, ' ')
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
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-foreground capitalize">
                    {eventLabel(event.event_type)}
                  </p>
                  <Chip
                    size="sm"
                    variant="soft"
                    color={event.source === 'fingerprint' ? 'accent' : 'default'}
                  >
                    {event.source === 'fingerprint' ? 'FP' : 'Track'}
                  </Chip>
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
