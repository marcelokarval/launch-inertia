import { Chip, Card } from '@heroui/react';
import { MessageCircle, Phone } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { PhoneChannelListItem, HubPrefixHint, Pagination } from '@/types';
import { PaginationControls } from '.';

interface Props {
  phones: PhoneChannelListItem[];
  prefixHints: HubPrefixHint[];
  pagination: Pagination;
}

export function HubPhonesTab({ phones, prefixHints, pagination }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <p className="text-sm text-default-500">
        {t('identities.hub.phoneCount', '{{count}} verified phones', { count: pagination.total })}
      </p>

      {/* Phone Table */}
      {phones.length > 0 ? (
        <Card className="border border-default-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-divider bg-default-50">
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                  {t('identities.hub.phone', 'Phone')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase hidden md:table-cell">
                  {t('identities.hub.owner', 'Owner')}
                </th>
                <th className="py-3 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                  {t('identities.hub.type', 'Type')}
                </th>
                <th className="py-3 px-4 text-center text-xs font-semibold text-default-500 uppercase hidden lg:table-cell">
                  {t('identities.hub.capabilities', 'Capabilities')}
                </th>
                <th className="py-3 px-4 text-right text-xs font-semibold text-default-500 uppercase hidden lg:table-cell">
                  {t('identities.hub.lastSeen', 'Last Seen')}
                </th>
              </tr>
            </thead>
            <tbody>
              {phones.map((phone) => (
                <tr key={phone.id} className="border-b border-divider last:border-0 hover:bg-default-50">
                  <td className="py-3 px-4">
                    <p className="text-sm font-medium text-foreground">{phone.display_value}</p>
                    <p className="text-xs text-default-400">+{phone.country_code}</p>
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <span className="text-sm text-default-500">
                      {phone.identity_name || phone.identity_id || '-'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <Chip variant="soft" size="sm" color="default">{phone.phone_type}</Chip>
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell">
                    <div className="flex items-center justify-center gap-2">
                      {phone.is_whatsapp && (
                        <span className="flex items-center gap-1 text-xs text-success">
                          <MessageCircle className="w-3 h-3" /> WA
                        </span>
                      )}
                      {phone.is_sms_capable && (
                        <span className="flex items-center gap-1 text-xs text-primary">
                          <Phone className="w-3 h-3" /> SMS
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right hidden lg:table-cell">
                    <span className="text-xs text-default-400">
                      {phone.last_seen ? new Date(phone.last_seen).toLocaleDateString() : '-'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      {/* Prefix Hints */}
      {prefixHints.length > 0 && (
        <Card className="border border-default-200">
          <Card.Header className="px-4 py-3 border-b border-divider">
            <span className="text-sm font-semibold">
              {t('identities.hub.prefixHintsTitle', 'Prefix Hints (from form intents)')}
            </span>
          </Card.Header>
          <Card.Content className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-divider bg-default-50">
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                    {t('identities.hub.prefix', 'Prefix')}
                  </th>
                  <th className="py-2 px-4 text-left text-xs font-semibold text-default-500 uppercase">
                    {t('identities.hub.seenBy', 'Seen By')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {prefixHints.map((hint) => (
                  <tr key={hint.prefix} className="border-b border-divider last:border-0">
                    <td className="py-2 px-4 text-sm text-foreground font-mono">+{hint.prefix}</td>
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

      {phones.length === 0 && prefixHints.length === 0 && (
        <Card className="border border-default-200">
          <Card.Content className="p-8 text-center">
            <p className="text-default-400">{t('identities.hub.noPhones', 'No phone channels yet')}</p>
          </Card.Content>
        </Card>
      )}

      {pagination.pages > 1 && <PaginationControls pagination={pagination} onPageChange={() => {}} />}
    </div>
  );
}
