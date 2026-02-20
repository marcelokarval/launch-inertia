/**
 * AuthLayout - Shared auth layout for Login, Register, ForgotPassword, ResetPassword.
 *
 * Split-panel design:
 *  - Left: gradient branding with feature list (desktop) / below form (mobile)
 *  - Right: form content inside a HeroUI Card
 */

import { type ReactNode } from 'react'
import { usePage } from '@inertiajs/react'
import { Card } from '@heroui/react'
import { Rocket, Target, BarChart3, Users, Zap, CheckCircle2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { LanguageSelector } from '@/components/ui/LanguageSelector'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { FlashMessages } from '@/components/shared/FlashMessages'
import type { PageProps } from '@/types/inertia'

const featureIcons = [Target, BarChart3, Users, Zap]
const featureKeys = [
  'authLayout.features.campaignManagement',
  'authLayout.features.analytics',
  'authLayout.features.leadManagement',
  'authLayout.features.automations',
]

interface Props {
  children: ReactNode
  title?: string
  subtitle?: string
}

export default function AuthLayout({ children, title, subtitle }: Props) {
  const { flash } = usePage<PageProps>().props
  const { t } = useTranslation('components')
  const { t: tc } = useTranslation('common')

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* ----- Left Panel: Branding & Features ----- */}
      <div className="order-2 lg:order-1 lg:flex-1 bg-gradient-brand relative overflow-hidden flex">
        {/* Grid pattern overlay */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />

        <div className="relative z-10 flex flex-col justify-center items-center lg:items-start px-8 lg:px-12 py-12 text-white w-full">
          <div className="space-y-8 max-w-lg w-full">
            {/* Logo & Title */}
            <div className="space-y-4 text-center lg:text-left">
              <div className="hidden lg:flex items-center space-x-3">
                <div className="p-3 rounded-xl bg-background/10 backdrop-blur-sm">
                  <Rocket className="h-8 w-8" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold">{tc('brand.name')}</h1>
                  <p className="text-lg opacity-90">{tc('brand.version')}</p>
                </div>
              </div>

              {/* Mobile compact logo */}
              <div className="lg:hidden flex flex-col items-center space-y-2">
                <div className="p-3 rounded-xl bg-background/10 backdrop-blur-sm">
                  <Rocket className="h-8 w-8" />
                </div>
                <h2 className="text-2xl font-bold">{t('authLayout.features.title')}</h2>
              </div>

              <p className="text-lg lg:text-xl opacity-90 max-w-md mx-auto lg:mx-0">
                {t('authLayout.features.subtitle')}
              </p>
            </div>

            {/* Features */}
            <div className="grid gap-6 w-full">
              {featureKeys.map((key, index) => {
                const Icon = featureIcons[index]
                return (
                  <div
                    key={key}
                    className="flex items-start space-x-4"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="p-2 rounded-lg bg-background/10 backdrop-blur-sm flex-shrink-0">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-success-300" />
                        {t(`${key}.title`)}
                      </h3>
                      <p className="text-sm opacity-80">{t(`${key}.description`)}</p>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Stats */}
            <div className="pt-8 border-t border-background/20">
              <div className="flex items-center justify-center lg:justify-start space-x-8">
                <div className="text-center lg:text-left">
                  <p className="text-3xl font-bold">+127%</p>
                  <p className="text-sm opacity-80">{t('authLayout.stats.avgRoi')}</p>
                </div>
                <div className="text-center lg:text-left">
                  <p className="text-3xl font-bold">2.4k</p>
                  <p className="text-sm opacity-80">{t('authLayout.stats.launches')}</p>
                </div>
                <div className="text-center lg:text-left">
                  <p className="text-3xl font-bold">99.9%</p>
                  <p className="text-sm opacity-80">{t('authLayout.stats.uptime')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative blurred circles */}
        <div className="absolute top-20 right-20 w-64 h-64 bg-background/5 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-20 w-96 h-96 bg-background/5 rounded-full blur-3xl" />
      </div>

      {/* ----- Right Panel: Form ----- */}
      <div className="order-1 lg:order-2 flex-1 flex items-center justify-center bg-background p-8 relative">
        {/* Header controls */}
        <div className="absolute top-4 right-4 flex items-center gap-1">
          <LanguageSelector />
          <ThemeToggle />
        </div>

        <div className="w-full max-w-md space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden text-center space-y-4">
            <div className="flex justify-center">
              <div className="p-3 rounded-xl bg-gradient-brand">
                <Rocket className="h-8 w-8 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                {tc('brand.name')}
              </h1>
              <p className="text-default-500">{tc('brand.version')}</p>
            </div>
          </div>

          {/* Flash messages */}
          <FlashMessages flash={flash} className="" />

          {/* Form card */}
          <Card className="w-full shadow-xl border border-default-200">
            {(title || subtitle) && (
              <Card.Header className="p-8 pb-6">
                <div className="space-y-2">
                  {title && (
                    <Card.Title className="text-2xl font-bold tracking-tight text-foreground">
                      {title}
                    </Card.Title>
                  )}
                  {subtitle && (
                    <Card.Description className="text-sm text-default-500">
                      {subtitle}
                    </Card.Description>
                  )}
                </div>
              </Card.Header>
            )}

            <Card.Content className="p-8 pt-0">{children}</Card.Content>
          </Card>

          {/* Footer */}
          <div className="text-center text-sm text-default-400">
            <p>{tc('brand.copyright', { year: new Date().getFullYear() })}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
