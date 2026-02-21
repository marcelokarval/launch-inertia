/**
 * Email channels list for the Identity detail tabs.
 *
 * When no emails exist but intent hints have email domains,
 * shows those as "known hints" instead of a bare empty state.
 */

import { Chip } from '@heroui/react'
import { Mail, CheckCircle, Clock, AtSign } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ChannelEmail } from '@/types'

interface Props {
  emails: ChannelEmail[]
  /** Email domain hints from form_intent events. */
  emailDomainHints?: string[]
}

export function EmailChannelsSection({ emails, emailDomainHints = [] }: Props) {
  const { t } = useTranslation()

  if (emails.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Mail className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.channels.noEmails', 'No email channels')}</p>
        {emailDomainHints.length > 0 && (
          <div className="mt-4 pt-4 border-t border-default-200">
            <div className="flex items-center justify-center gap-2 mb-2">
              <AtSign className="w-4 h-4 text-default-400" />
              <span className="text-xs text-default-500">
                {t('identities.show.channels.knownDomains', 'Known email domains from form activity')}
              </span>
            </div>
            <div className="flex items-center justify-center gap-2 flex-wrap">
              {emailDomainHints.map((domain) => (
                <Chip key={domain} size="sm" variant="soft" color="accent">
                  @{domain}
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
      {emails.map((email) => (
        <div
          key={email.id}
          className="flex items-center justify-between p-4 rounded-lg border border-default-200 hover:border-default-300 transition-colors"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className={`p-2 rounded-lg ${email.is_verified ? 'bg-success/10' : 'bg-default-100'}`}>
              <Mail className={`w-4 h-4 ${email.is_verified ? 'text-success' : 'text-default-400'}`} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{email.value}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-default-400">{email.domain}</span>
                {email.is_dnc && (
                  <Chip color="danger" variant="soft" size="sm" className="text-[10px] h-4">
                    DNC
                  </Chip>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Chip
              color={EMAIL_LIFECYCLE_CHIP_COLOR[email.lifecycle_status]}
              variant="soft"
              size="sm"
            >
              {email.lifecycle_status}
            </Chip>
            {email.is_verified ? (
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

// Re-export for convenience
import { EMAIL_LIFECYCLE_CHIP_COLOR } from '@/types'
