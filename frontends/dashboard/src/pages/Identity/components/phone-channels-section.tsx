/**
 * Phone channels list for the Identity detail tabs.
 */

import { Chip } from '@heroui/react'
import { Phone, CheckCircle, Clock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ChannelPhone } from '@/types'

interface Props {
  phones: ChannelPhone[]
}

export function PhoneChannelsSection({ phones }: Props) {
  const { t } = useTranslation()

  if (phones.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Phone className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.channels.noPhones', 'No phone channels')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {phones.map((phone) => (
        <div
          key={phone.id}
          className="flex items-center justify-between p-4 rounded-lg border border-default-200 hover:border-default-300 transition-colors"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className={`p-2 rounded-lg ${phone.is_verified ? 'bg-success/10' : 'bg-default-100'}`}>
              <Phone className={`w-4 h-4 ${phone.is_verified ? 'text-success' : 'text-default-400'}`} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground">{phone.display_value}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-default-400 capitalize">{phone.phone_type}</span>
                {phone.is_whatsapp && (
                  <Chip color="success" variant="soft" size="sm" className="text-[10px] h-4">
                    WhatsApp
                  </Chip>
                )}
                {phone.is_dnc && (
                  <Chip color="danger" variant="soft" size="sm" className="text-[10px] h-4">
                    DNC
                  </Chip>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {phone.is_verified ? (
              <CheckCircle className="w-4 h-4 text-success" />
            ) : (
              <Clock className="w-4 h-4 text-default-300" />
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
