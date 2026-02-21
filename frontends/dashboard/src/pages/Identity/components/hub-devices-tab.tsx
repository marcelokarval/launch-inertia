import { Card, Chip } from '@heroui/react';
import { Monitor, Smartphone, Fingerprint } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { DeviceListItem, FingerprintListItem } from '@/types';

interface Props {
  devices: DeviceListItem[];
  fingerprints: FingerprintListItem[];
}

export function HubDevicesTab({ devices, fingerprints }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <p className="text-sm text-default-500">
        {t('identities.hub.deviceCount', '{{count}} device profiles', { count: devices.length })}
      </p>

      {/* Device Profiles */}
      {devices.length > 0 ? (
        <Card className="border border-default-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-divider bg-default-50">
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                  {t('identities.hub.device', 'Device')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase hidden md:table-cell">
                  {t('identities.hub.identitiesLinked', 'Identities')}
                </th>
                <th className="py-3 px-4 text-right text-xs font-semibold text-default-500 uppercase">
                  {t('identities.hub.events', 'Events')}
                </th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device) => (
                <tr key={device.id} className="border-b border-divider last:border-0 hover:bg-default-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {device.device_type === 'mobile' ? (
                        <Smartphone className="w-4 h-4 text-default-400" />
                      ) : (
                        <Monitor className="w-4 h-4 text-default-400" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {device.browser_family} {device.browser_version}
                        </p>
                        <p className="text-xs text-default-400">
                          {device.os_family} {device.os_version} / {device.device_type}
                          {device.device_brand && ` / ${device.device_brand}`}
                        </p>
                      </div>
                    </div>
                    {device.is_bot && (
                      <Chip variant="soft" color="warning" size="sm" className="mt-1">Bot</Chip>
                    )}
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <span className="text-sm text-default-500">
                      {device.identity_ids.length} {t('identities.hub.identitiesCount', 'identities')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="text-sm font-medium text-foreground">{device.event_count}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : (
        <Card className="border border-default-200">
          <Card.Content className="p-8 text-center">
            <p className="text-default-400">{t('identities.hub.noDevices', 'No device profiles yet')}</p>
          </Card.Content>
        </Card>
      )}

      {/* FingerprintJS Identities */}
      <Card className="border border-default-200">
        <Card.Header className="px-4 py-3 border-b border-divider">
          <div className="flex items-center gap-2">
            <Fingerprint className="w-4 h-4 text-default-500" />
            <span className="text-sm font-semibold">
              {t('identities.hub.fingerprintTitle', 'FingerprintJS Pro Identities')}
            </span>
          </div>
        </Card.Header>
        <Card.Content className="p-0">
          {fingerprints.length === 0 ? (
            <div className="p-4">
              <p className="text-sm text-default-400">
                {t('identities.hub.noFingerprints', 'No FingerprintJS records. Configure FINGERPRINT_API_KEY in .env.')}
              </p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-divider bg-default-50">
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase">Hash</th>
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase hidden md:table-cell">
                    {t('identities.hub.browser', 'Browser')}
                  </th>
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase hidden md:table-cell">
                    {t('identities.hub.owner', 'Owner')}
                  </th>
                  <th className="py-2 px-4 text-right text-xs font-semibold text-default-500 uppercase">
                    {t('identities.hub.confidence', 'Confidence')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {fingerprints.map((fp) => (
                  <tr key={fp.id} className="border-b border-divider last:border-0">
                    <td className="py-2 px-4 text-sm font-mono text-foreground">{fp.hash}</td>
                    <td className="py-2 px-4 text-sm text-default-500 hidden md:table-cell">
                      {fp.browser} / {fp.os}
                    </td>
                    <td className="py-2 px-4 text-sm text-default-500 hidden md:table-cell">
                      {fp.identity_name || fp.identity_id || '-'}
                    </td>
                    <td className="py-2 px-4 text-right text-sm text-default-500">
                      {(fp.confidence_score * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
