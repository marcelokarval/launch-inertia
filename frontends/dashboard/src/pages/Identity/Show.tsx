import { Head, Link } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip, Tabs } from '@heroui/react'
import { Button } from '@/components/ui'
import {
  User, Mail, Phone, Shield, Fingerprint, Globe, Monitor, Smartphone, Tablet,
  CheckCircle, AlertTriangle, Clock, Tag, ExternalLink,
  Activity, TrendingUp, Eye, MapPin, Wifi,
  Edit, Trash2, ArrowLeft, Calendar, FileText,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type {
  IdentityDetail, ChannelEmail, ChannelPhone, DeviceFingerprint,
  Attribution, TimelineEvent, Tag as TagType,
} from '@/types'
import { EMAIL_LIFECYCLE_CHIP_COLOR, IDENTITY_STATUS_CHIP_COLOR } from '@/types'

// ============================================================================
// Types
// ============================================================================

interface IdentityShowData extends IdentityDetail {
  display_name: string
  operator_notes: string
  tags: TagType[]
  lifecycle_global: Record<string, unknown>
  attributions: Attribution[]
  timeline: TimelineEvent[]
}

interface Props {
  identity: IdentityShowData
}

// ============================================================================
// Confidence Score Badge
// ============================================================================

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const chipColor: 'success' | 'warning' | 'danger' = pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger'

  return (
    <Chip color={chipColor} variant="soft" size="sm">
      <span className="inline-flex items-center gap-1">
        <Shield className="w-3.5 h-3.5" />
        {pct}%
      </span>
    </Chip>
  )
}

// ============================================================================
// Identity Info Sidebar Card
// ============================================================================

function IdentityInfoCard({ identity }: { identity: IdentityShowData }) {
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
              <p className="text-sm text-default-600 whitespace-pre-wrap">{identity.operator_notes}</p>
            </div>
          )}

          {/* Dates */}
          <div className="pt-3 border-t border-divider space-y-2">
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-default-400 flex-shrink-0" />
              <div>
                <p className="text-xs text-default-400">{t('identities.show.createdAt', 'Created')}</p>
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
                  <p className="text-xs text-default-400">{t('identities.show.lastSeen', 'Last Seen')}</p>
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

// ============================================================================
// Stats Card
// ============================================================================

function StatsCard({ identity }: { identity: IdentityShowData }) {
  const { t } = useTranslation()

  return (
    <Card className="border border-default-200">
      <Card.Content className="p-6">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-lg bg-content2">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Mail className="w-4 h-4 text-primary" />
              <span className="text-2xl font-bold text-foreground">{identity.email_count}</span>
            </div>
            <p className="text-xs text-default-500">{t('identities.show.stats.emails', 'Emails')}</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-content2">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Phone className="w-4 h-4 text-success" />
              <span className="text-2xl font-bold text-foreground">{identity.phone_count}</span>
            </div>
            <p className="text-xs text-default-500">{t('identities.show.stats.phones', 'Phones')}</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-content2">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Fingerprint className="w-4 h-4 text-warning" />
              <span className="text-2xl font-bold text-foreground">{identity.fingerprint_count}</span>
            </div>
            <p className="text-xs text-default-500">{t('identities.show.stats.devices', 'Devices')}</p>
          </div>
        </div>
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// Email Channels Section
// ============================================================================

function EmailChannelsSection({ emails }: { emails: ChannelEmail[] }) {
  const { t } = useTranslation()

  if (emails.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Mail className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.channels.noEmails', 'No email channels')}</p>
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

// ============================================================================
// Phone Channels Section
// ============================================================================

function PhoneChannelsSection({ phones }: { phones: ChannelPhone[] }) {
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

// ============================================================================
// Devices / Fingerprints Section
// ============================================================================

function DeviceIcon({ type }: { type: string }) {
  if (type === 'mobile') return <Smartphone className="w-4 h-4" />
  if (type === 'tablet') return <Tablet className="w-4 h-4" />
  return <Monitor className="w-4 h-4" />
}

function DevicesSection({ fingerprints }: { fingerprints: DeviceFingerprint[] }) {
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

// ============================================================================
// Attributions Section
// ============================================================================

function AttributionsSection({ attributions }: { attributions: Attribution[] }) {
  const { t } = useTranslation()

  if (attributions.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.attributions.noData', 'No attribution data')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {attributions.map((attr) => (
        <div
          key={attr.id}
          className="p-4 rounded-lg border border-default-200"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                {attr.utm_source && (
                  <Chip variant="soft" size="sm" color="accent">
                    {attr.utm_source}
                  </Chip>
                )}
                {attr.utm_medium && (
                  <Chip variant="soft" size="sm" color="default">
                    {attr.utm_medium}
                  </Chip>
                )}
                {attr.utm_campaign && (
                  <Chip variant="soft" size="sm" color="warning">
                    {attr.utm_campaign}
                  </Chip>
                )}
              </div>
              {attr.landing_page && (
                <p className="text-xs text-default-400 mt-2 flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" />
                  {attr.landing_page}
                </p>
              )}
              {attr.referrer && (
                <p className="text-xs text-default-400 mt-1 flex items-center gap-1">
                  <Globe className="w-3 h-3" />
                  {attr.referrer}
                </p>
              )}
            </div>
            <div className="text-right text-xs text-default-400 whitespace-nowrap">
              <Chip variant="soft" size="sm" color="default">{attr.touchpoint_type}</Chip>
              <p className="mt-1">{new Date(attr.created_at).toLocaleDateString('pt-BR')}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// Timeline Section
// ============================================================================

function TimelineSection({ events }: { events: TimelineEvent[] }) {
  const { t } = useTranslation()

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-default-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>{t('identities.show.timeline.noEvents', 'No events recorded')}</p>
      </div>
    )
  }

  const eventIcon = (type: string) => {
    if (type === 'page_view') return <Eye className="w-3.5 h-3.5 text-primary" />
    if (type === 'form_submit') return <Edit className="w-3.5 h-3.5 text-success" />
    if (type === 'click') return <ExternalLink className="w-3.5 h-3.5 text-warning" />
    return <Activity className="w-3.5 h-3.5 text-default-400" />
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-[17px] top-6 bottom-6 w-px bg-default-200" />

      <div className="space-y-4">
        {events.map((event) => (
          <div key={event.id} className="flex items-start gap-3 relative">
            <div className="w-[35px] h-[35px] rounded-full bg-content2 border border-default-200 flex items-center justify-center flex-shrink-0 z-10">
              {eventIcon(event.event_type)}
            </div>
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-foreground capitalize">
                  {event.event_type.replace('_', ' ')}
                </p>
                <span className="text-xs text-default-400 whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleString('pt-BR', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
              {event.page_url && (
                <p className="text-xs text-default-400 truncate mt-0.5">
                  {event.page_url}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function IdentityShow({ identity }: Props) {
  const { t } = useTranslation()

  return (
    <DashboardLayout title={identity.display_name || identity.id}>
      <Head title={identity.display_name || identity.id} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link
            href="/app/identities/"
            className="p-2 rounded-lg hover:bg-default-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              {identity.display_name || identity.id}
            </h2>
            {identity.first_seen_source && (
              <p className="text-default-500 text-sm">
                {t('identities.show.firstSource', 'First seen via')}: {identity.first_seen_source}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href={`/app/identities/${identity.id}/edit/`}>
            <Button variant="primary">
              <Edit className="w-4 h-4" />
              {t('identities.show.edit', 'Edit')}
            </Button>
          </Link>
          <Link href={`/app/identities/${identity.id}/delete/`}>
            <Button variant="danger">
              <Trash2 className="w-4 h-4" />
              {t('identities.show.delete', 'Delete')}
            </Button>
          </Link>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Identity info + Stats */}
        <div className="lg:col-span-1 space-y-6">
          <IdentityInfoCard identity={identity} />
          <StatsCard identity={identity} />
        </div>

        {/* Right column: Tabbed detail sections */}
        <div className="lg:col-span-2">
          <Card className="border border-default-200">
            <Card.Content className="p-0">
              <Tabs className="w-full">
                <Tabs.List className="px-4 pt-3 border-b border-divider">
                  <Tabs.Tab id="emails">
                    <div className="flex items-center gap-1.5">
                      <Mail className="w-4 h-4" />
                      <span>{t('identities.show.tabs.emails', 'Emails')}</span>
                      <Chip size="sm" variant="soft" color="default">{identity.email_count}</Chip>
                    </div>
                  </Tabs.Tab>
                  <Tabs.Tab id="phones">
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-4 h-4" />
                      <span>{t('identities.show.tabs.phones', 'Phones')}</span>
                      <Chip size="sm" variant="soft" color="default">{identity.phone_count}</Chip>
                    </div>
                  </Tabs.Tab>
                  <Tabs.Tab id="devices">
                    <div className="flex items-center gap-1.5">
                      <Fingerprint className="w-4 h-4" />
                      <span>{t('identities.show.tabs.devices', 'Devices')}</span>
                      <Chip size="sm" variant="soft" color="default">{identity.fingerprint_count}</Chip>
                    </div>
                  </Tabs.Tab>
                  <Tabs.Tab id="attributions">
                    <div className="flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4" />
                      <span>{t('identities.show.tabs.attributions', 'Attribution')}</span>
                      {identity.attributions.length > 0 && (
                        <Chip size="sm" variant="soft" color="default">{identity.attributions.length}</Chip>
                      )}
                    </div>
                  </Tabs.Tab>
                  <Tabs.Tab id="timeline">
                    <div className="flex items-center gap-1.5">
                      <Activity className="w-4 h-4" />
                      <span>{t('identities.show.tabs.timeline', 'Timeline')}</span>
                      {identity.timeline.length > 0 && (
                        <Chip size="sm" variant="soft" color="default">{identity.timeline.length}</Chip>
                      )}
                    </div>
                  </Tabs.Tab>
                </Tabs.List>

                <div className="p-4">
                  <Tabs.Panel id="emails">
                    <EmailChannelsSection emails={identity.emails ?? []} />
                  </Tabs.Panel>
                  <Tabs.Panel id="phones">
                    <PhoneChannelsSection phones={identity.phones ?? []} />
                  </Tabs.Panel>
                  <Tabs.Panel id="devices">
                    <DevicesSection fingerprints={identity.fingerprints ?? []} />
                  </Tabs.Panel>
                  <Tabs.Panel id="attributions">
                    <AttributionsSection attributions={identity.attributions} />
                  </Tabs.Panel>
                  <Tabs.Panel id="timeline">
                    <TimelineSection events={identity.timeline} />
                  </Tabs.Panel>
                </div>
              </Tabs>
            </Card.Content>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
