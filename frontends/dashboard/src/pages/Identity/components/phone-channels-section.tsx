/**
 * Phone channels list for the Identity detail tabs.
 *
 * When no phones exist but intent hints have phone prefixes,
 * shows those as "known hints" instead of a bare empty state.
 */

import { Chip } from '@heroui/react'
import { Phone, CheckCircle, Clock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ChannelPhone } from '@/types'

interface Props {
  phones: ChannelPhone[]
  /** Phone prefix hints from form_intent events. */
  phonePrefixHints?: string[]
}

export function PhoneChannelsSection({ phones, phonePrefixHints = [] }: Props) {
  const { t } = useTranslation()

  if (phones.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Phone className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.channels.noPhones', 'No phone channels')}</p>
        {phonePrefixHints.length > 0 && (
          <div className="mt-4 pt-4 border-t border-default-200">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Phone className="w-4 h-4 text-default-400" />
              <span className="text-xs text-default-500">
                {t('identities.show.channels.knownPrefixes', 'Known phone prefixes from form activity')}
              </span>
            </div>
            <div className="flex items-center justify-center gap-2 flex-wrap">
              {phonePrefixHints.map((prefix) => (
                <Chip key={prefix} size="sm" variant="soft" color="success">
                  {prefix}...
                </Chip>
              ))}
            </div>
          </div>
        )}
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
