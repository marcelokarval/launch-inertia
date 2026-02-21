import { Chip, Card } from '@heroui/react';
import { useTranslation } from 'react-i18next';
import type { EmailChannelListItem, HubDomainHint, Pagination } from '@/types';
import { EMAIL_LIFECYCLE_CHIP_COLOR } from '@/types';
import { PaginationControls } from '.';

interface Props {
  emails: EmailChannelListItem[];
  domainHints: HubDomainHint[];
  pagination: Pagination;
}

export function HubEmailsTab({ emails, domainHints, pagination }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <p className="text-sm text-default-500">
        {t('identities.hub.emailCount', '{{count}} verified emails', { count: pagination.total })}
      </p>

      {/* Email Table */}
      {emails.length > 0 ? (
        <Card className="border border-default-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-divider bg-default-50">
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                  {t('identities.hub.email', 'Email')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase hidden md:table-cell">
                  {t('identities.hub.owner', 'Owner')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                  {t('identities.hub.status', 'Status')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase hidden lg:table-cell">
                  {t('identities.hub.quality', 'Quality')}
                </th>
                <th className="py-3 px-4 text-right text-xs font-semibold text-default-500 uppercase hidden lg:table-cell">
                  {t('identities.hub.lastSeen', 'Last Seen')}
                </th>
              </tr>
            </thead>
            <tbody>
              {emails.map((email) => (
                <tr key={email.id} className="border-b border-divider last:border-0 hover:bg-default-50">
                  <td className="py-3 px-4">
                    <p className="text-sm font-medium text-foreground">{email.value}</p>
                    <p className="text-xs text-default-400">{email.domain}</p>
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <span className="text-sm text-default-500">
                      {email.identity_name || email.identity_id || '-'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <Chip
                      color={EMAIL_LIFECYCLE_CHIP_COLOR[email.lifecycle_status] ?? 'default'}
                      variant="soft"
                      size="sm"
                    >
                      {email.lifecycle_status}
                    </Chip>
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell">
                    <span className="text-sm text-default-500">{email.quality_score.toFixed(1)}</span>
                  </td>
                  <td className="py-3 px-4 text-right hidden lg:table-cell">
                    <span className="text-xs text-default-400">
                      {email.last_seen ? new Date(email.last_seen).toLocaleDateString() : '-'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      {/* Domain Hints */}
      {domainHints.length > 0 && (
        <Card className="border border-default-200">
          <Card.Header className="px-4 py-3 border-b border-divider">
            <span className="text-sm font-semibold">
              {t('identities.hub.domainHintsTitle', 'Domain Hints (from form intents)')}
            </span>
          </Card.Header>
          <Card.Content className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-divider bg-default-50">
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                    {t('identities.hub.domain', 'Domain')}
                  </th>
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                    {t('identities.hub.seenBy', 'Seen By')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {domainHints.map((hint) => (
                  <tr key={hint.domain} className="border-b border-divider last:border-0">
                    <td className="py-2 px-4 text-sm text-foreground font-mono">{hint.domain}</td>
                    <td className="py-2 px-4 text-xs text-default-500">
                      {hint.identities.length} {t('identities.hub.identitiesCount', 'identities')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card.Content>
        </Card>
      )}

      {emails.length === 0 && domainHints.length === 0 && (
        <Card className="border border-default-200">
          <Card.Content className="p-8 text-center">
            <p className="text-default-400">{t('identities.hub.noEmails', 'No email channels yet')}</p>
          </Card.Content>
        </Card>
      )}

      {pagination.pages > 1 && <PaginationControls pagination={pagination} onPageChange={() => {}} />}
    </div>
  );
}
