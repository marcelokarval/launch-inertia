/**
 * Stats card — email / phone / device counts.
 */

import { Card } from '@heroui/react'
import { Mail, Phone, Fingerprint } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { IdentityShowData } from '@/types'

interface Props {
  identity: IdentityShowData
}

export function StatsCard({ identity }: Props) {
  const { t } = useTranslation()

  return (
    <Card className="border border-default-200">
      <Card.Content className="p-6">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-lg bg-content2">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Mail className="w-4 h-4 text-primary" />
              <span className="text-2xl font-bold text-foreground">
                {identity.email_count}
              </span>
            </div>
            <p className="text-xs text-default-500">
              {t('identities.show.stats.emails', 'Emails')}
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-content2">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Phone className="w-4 h-4 text-success" />
              <span className="text-2xl font-bold text-foreground">
                {identity.phone_count}
              </span>
            </div>
            <p className="text-xs text-default-500">
              {t('identities.show.stats.phones', 'Phones')}
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-content2">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Fingerprint className="w-4 h-4 text-warning" />
              <span className="text-2xl font-bold text-foreground">
                {identity.fingerprint_count}
              </span>
            </div>
            <p className="text-xs text-default-500">
              {t('identities.show.stats.devices', 'Devices')}
            </p>
          </div>
        </div>
      </Card.Content>
    </Card>
  )
}
