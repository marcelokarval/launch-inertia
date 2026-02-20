import { Head, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip, Tabs } from '@heroui/react'
import { Button } from '@/components/ui'
import { Mail, Phone, Fingerprint, TrendingUp, Activity, Edit, Trash2, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { IdentityShowData } from '@/types'
import {
  IdentityInfoCard,
  StatsCard,
  EmailChannelsSection,
  PhoneChannelsSection,
  DevicesSection,
  AttributionsSection,
  TimelineSection,
} from './components'

interface Props {
  identity: IdentityShowData
}

export default function IdentityShow({ identity }: Props) {
  const { t } = useTranslation()

  return (
    <DashboardLayout title={identity.display_name || identity.id}>
      <Head title={identity.display_name || identity.id} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onPress={() => router.visit('/app/identities/')}
          >
            <ArrowLeft className="w-5 h-5 text-default-500" />
          </Button>
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
          <Button
            variant="primary"
            onPress={() => router.visit(`/app/identities/${identity.id}/edit/`)}
          >
            <Edit className="w-4 h-4" />
            {t('identities.show.edit', 'Edit')}
          </Button>
          <Button
            variant="danger"
            onPress={() => router.visit(`/app/identities/${identity.id}/delete/`)}
          >
            <Trash2 className="w-4 h-4" />
            {t('identities.show.delete', 'Delete')}
          </Button>
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
