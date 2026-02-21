import { router } from '@inertiajs/react';
import { Chip, Avatar } from '@heroui/react';
import { Mail, Phone, User, Eye, Activity } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { IdentityListItem } from '@/types';
import { IDENTITY_STATUS_CHIP_COLOR } from '@/types';
import { ConfidenceBadge } from '@/components/shared/ConfidenceBadge';
import { ChannelCounts } from './ChannelCounts';
import { TagChips } from './TagChips';

interface IdentityRowProps {
  identity: IdentityListItem;
}

export function IdentityRow({ identity }: IdentityRowProps) {
  const { t } = useTranslation();

  const navigateToIdentity = () => {
    router.visit(`/app/identities/${identity.id}/`);
  };

  return (
    <tr
      className="cursor-pointer hover:bg-default-50 transition-colors border-b border-divider last:border-b-0"
      onClick={navigateToIdentity}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') navigateToIdentity(); }}
    >
      {/* Name + Contact */}
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <Avatar size="sm" className="bg-primary/10 flex-shrink-0">
            <Avatar.Fallback>
              <User className="w-4 h-4 text-primary" />
            </Avatar.Fallback>
          </Avatar>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-foreground truncate">
                {identity.display_name || t('identities.index.anonymous', 'Anonymous')}
              </p>
              <ConfidenceBadge score={identity.confidence_score} />
            </div>
            <div className="flex items-center gap-4 mt-0.5">
              {identity.primary_email && (
                <span className="flex items-center gap-1 text-xs text-default-500 truncate">
                  <Mail className="w-3 h-3 flex-shrink-0" />
                  {identity.primary_email}
                </span>
              )}
              {identity.primary_phone && (
                <span className="flex items-center gap-1 text-xs text-default-500">
                  <Phone className="w-3 h-3 flex-shrink-0" />
                  {identity.primary_phone}
                </span>
              )}
            </div>
          </div>
        </div>
      </td>

      {/* Channels */}
      <td className="py-3 px-4 hidden md:table-cell">
        <ChannelCounts
          emailCount={identity.email_count}
          phoneCount={identity.phone_count}
          fpCount={identity.fingerprint_count}
        />
      </td>

      {/* Activity Stats */}
      <td className="py-3 px-4 hidden lg:table-cell">
        <div className="flex items-center gap-3 text-xs text-default-500">
          <span className="flex items-center gap-1" title={t('identities.index.table.pageViews', 'Page views')}>
            <Eye className="w-3 h-3" />
            {identity.page_view_count}
          </span>
          <span className="flex items-center gap-1" title={t('identities.index.table.totalEvents', 'Total events')}>
            <Activity className="w-3 h-3" />
            {identity.total_event_count}
          </span>
        </div>
      </td>

      {/* Tags */}
      <td className="py-3 px-4 hidden xl:table-cell">
        <TagChips tags={identity.tags} />
      </td>

      {/* Status */}
      <td className="py-3 px-4">
        <Chip
          color={IDENTITY_STATUS_CHIP_COLOR[identity.status] ?? 'default'}
          variant="soft"
          size="sm"
        >
          {identity.status}
        </Chip>
      </td>

      {/* Last Seen */}
      <td className="py-3 px-4 hidden lg:table-cell text-right">
        {identity.last_seen ? (
          <span className="text-xs text-default-400">
            {new Date(identity.last_seen).toLocaleDateString()}
          </span>
        ) : (
          <span className="text-xs text-default-300">-</span>
        )}
      </td>
    </tr>
  );
}
