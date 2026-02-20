import { Head, router } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card } from '@heroui/react'
import { User, Bell, Shield, CreditCard, ChevronRight } from 'lucide-react'
import type { ComponentType } from 'react'
import type { SharedUser } from '@/types'

interface Props {
  user: SharedUser
}

interface SettingsLink {
  href: string
  icon: ComponentType<{ className?: string }>
  titleKey: string
  descriptionKey: string
}

const settingsLinks: SettingsLink[] = [
  {
    href: '/app/settings/profile/',
    icon: User,
    titleKey: 'settings.index.nav.profile',
    descriptionKey: 'settings.index.nav.profileDesc',
  },
  {
    href: '/app/notifications/',
    icon: Bell,
    titleKey: 'settings.index.nav.notifications',
    descriptionKey: 'settings.index.nav.notificationsDesc',
  },
  {
    href: '/app/billing/',
    icon: CreditCard,
    titleKey: 'settings.index.nav.billing',
    descriptionKey: 'settings.index.nav.billingDesc',
  },
  {
    href: '/app/settings/security/',
    icon: Shield,
    titleKey: 'settings.index.nav.security',
    descriptionKey: 'settings.index.nav.securityDesc',
  },
]

export default function SettingsIndex(_props: Props) {
  const { t } = useTranslation()

  return (
    <DashboardLayout title={t('settings.index.title')}>
      <Head title={t('settings.index.pageTitle')} />

      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-foreground">
            {t('settings.index.title')}
          </h2>
          <p className="mt-1 text-default-500">
            {t('settings.index.description')}
          </p>
        </div>

        <div className="space-y-4">
          {settingsLinks.map((link) => (
            <Card
              key={link.href}
              className="border border-default-200 cursor-pointer hover:bg-default-100 transition-colors"
              onClick={() => router.visit(link.href)}
            >
              <Card.Content className="p-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <link.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground">
                      {t(link.titleKey)}
                    </h3>
                    <p className="text-sm text-default-500">
                      {t(link.descriptionKey)}
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-default-400" />
                </div>
              </Card.Content>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  )
}
