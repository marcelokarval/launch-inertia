/**
 * Device fingerprints list for the Identity detail tabs.
 */

import { Chip } from '@heroui/react'
import {
  Monitor, Smartphone, Tablet, Fingerprint,
  AlertTriangle, Wifi, MapPin,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { DeviceFingerprint } from '@/types'

function DeviceIcon({ type }: { type: string }) {
  if (type === 'mobile') return <Smartphone className="w-4 h-4" />
  if (type === 'tablet') return <Tablet className="w-4 h-4" />
  return <Monitor className="w-4 h-4" />
}

interface Props {
  fingerprints: DeviceFingerprint[]
}

export function DevicesSection({ fingerprints }: Props) {
  const { t } = useTranslation()

  if (fingerprints.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Fingerprint className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.devices.noDevices', 'No devices tracked')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {fingerprints.map((fp) => {
        const hasFraud = fp.fraud_signals.length > 0
        return (
          <div
            key={fp.id}
            className={`p-4 rounded-lg border transition-colors ${
              hasFraud
                ? 'border-warning/50 bg-warning/5'
                : 'border-default-200 hover:border-default-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${fp.is_master ? 'bg-primary/10' : 'bg-default-100'}`}>
                  <DeviceIcon type={fp.device_type} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-foreground">
                      {fp.browser_family} {fp.os ? `/ ${fp.os}` : ''}
                    </p>
                    {fp.is_master && (
                      <Chip color="accent" variant="soft" size="sm" className="text-[10px] h-4">
                        {t('identities.show.devices.primary', 'Primary')}
                      </Chip>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-default-400">
                    <span className="capitalize">{fp.device_type}</span>
                    {fp.ip_address && (
                      <span className="flex items-center gap-1">
                        <Wifi className="w-3 h-3" />
                        {fp.ip_address}
                      </span>
                    )}
                    {fp.geo_info?.country ? (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {`${fp.geo_info.city ?? ''} ${fp.geo_info.country ?? ''}`.trim()}
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-foreground">
                  {Math.round(fp.confidence_score * 100)}%
                </div>
                <p className="text-xs text-default-400">
                  {t('identities.show.devices.fpConfidence', 'FP confidence')}
                </p>
              </div>
            </div>

            {/* Fraud signals */}
            {hasFraud && (
              <div className="mt-3 pt-3 border-t border-warning/20">
                <div className="flex flex-wrap gap-2">
                  {fp.fraud_signals.map((signal, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-1 text-xs text-warning"
                    >
                      <AlertTriangle className="w-3 h-3" />
                      <span>{signal.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
