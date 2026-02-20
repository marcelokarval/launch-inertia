/**
 * Attribution touchpoints for the Identity detail tabs.
 */

import { Chip } from '@heroui/react'
import { TrendingUp, ExternalLink, Globe } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Attribution } from '@/types'

interface Props {
  attributions: Attribution[]
}

export function AttributionsSection({ attributions }: Props) {
  const { t } = useTranslation()

  if (attributions.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.attributions.noData', 'No attribution data')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {attributions.map((attr) => (
        <div
          key={attr.id}
          className="p-4 rounded-lg border border-default-200"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                {attr.utm_source && (
                  <Chip variant="soft" size="sm" color="accent">
                    {attr.utm_source}
                  </Chip>
                )}
                {attr.utm_medium && (
                  <Chip variant="soft" size="sm" color="default">
                    {attr.utm_medium}
                  </Chip>
                )}
                {attr.utm_campaign && (
                  <Chip variant="soft" size="sm" color="warning">
                    {attr.utm_campaign}
                  </Chip>
                )}
              </div>
              {attr.landing_page && (
                <p className="text-xs text-default-400 mt-2 flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" />
                  {attr.landing_page}
                </p>
              )}
              {attr.referrer && (
                <p className="text-xs text-default-400 mt-1 flex items-center gap-1">
                  <Globe className="w-3 h-3" />
                  {attr.referrer}
                </p>
              )}
            </div>
            <div className="text-right text-xs text-default-400 whitespace-nowrap">
              <Chip variant="soft" size="sm" color="default">{attr.touchpoint_type}</Chip>
              <p className="mt-1">
                {new Date(attr.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
