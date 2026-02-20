/**
 * Identity sidebar card — avatar, status, tags, notes, dates.
 */

import { Card, Chip } from '@heroui/react'
import { User, Tag, FileText, Calendar, Eye } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { IdentityShowData } from '@/types'
import { IDENTITY_STATUS_CHIP_COLOR } from '@/types'
import { ConfidenceBadge } from '@/components/shared/ConfidenceBadge'

interface Props {
  identity: IdentityShowData
}

export function IdentityInfoCard({ identity }: Props) {
  const { t } = useTranslation()

  return (
    <Card className="border border-default-200">
      <Card.Content className="p-6">
        <div className="space-y-4">
          {/* Avatar & Name */}
          <div className="flex items-center gap-4 pb-4 border-b border-divider">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <User className="w-8 h-8 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-xl font-semibold text-foreground truncate">
                {identity.display_name || identity.id}
              </h3>
              <div className="flex items-center gap-2 mt-1.5">
                <Chip
                  color={IDENTITY_STATUS_CHIP_COLOR[identity.status]}
                  variant="soft"
                  size="sm"
                >
                  {identity.status}
                </Chip>
                <ConfidenceBadge score={identity.confidence_score} />
              </div>
            </div>
          </div>

          {/* Tags */}
          {identity.tags && identity.tags.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Tag className="w-4 h-4 text-default-400 flex-shrink-0" />
              {identity.tags.map((tag) => (
                <Chip
                  key={tag.id}
                  size="sm"
                  variant="soft"
                  style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                >
                  {tag.name}
                </Chip>
              ))}
            </div>
          )}

          {/* Operator Notes */}
          {identity.operator_notes && (
            <div className="pt-3 border-t border-divider">
              <h4 className="text-sm font-semibold text-foreground mb-1 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-default-400" />
                {t('identities.show.operatorNotes', 'Operator Notes')}
              </h4>
              <p className="text-sm text-default-600 whitespace-pre-wrap">
                {identity.operator_notes}
              </p>
            </div>
          )}

          {/* Dates */}
          <div className="pt-3 border-t border-divider space-y-2">
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-default-400 flex-shrink-0" />
              <div>
                <p className="text-xs text-default-400">
                  {t('identities.show.createdAt', 'Created')}
                </p>
                <p className="text-sm text-foreground">
                  {identity.created_at
                    ? new Date(identity.created_at).toLocaleDateString('pt-BR', {
                        day: '2-digit', month: 'long', year: 'numeric',
                      })
                    : '-'}
                </p>
              </div>
            </div>
            {identity.last_seen && (
              <div className="flex items-center gap-3">
                <Eye className="w-4 h-4 text-default-400 flex-shrink-0" />
                <div>
                  <p className="text-xs text-default-400">
                    {t('identities.show.lastSeen', 'Last Seen')}
                  </p>
                  <p className="text-sm text-foreground">
                    {new Date(identity.last_seen).toLocaleDateString('pt-BR', {
                      day: '2-digit', month: 'long', year: 'numeric',
                    })}
                  </p>
                </div>
              </div>
            )}
            {identity.first_seen_source && (
              <p className="text-xs text-default-400">
                {t('identities.show.firstSource', 'First seen via')}: {identity.first_seen_source}
              </p>
            )}
          </div>
        </div>
      </Card.Content>
    </Card>
  )
}
