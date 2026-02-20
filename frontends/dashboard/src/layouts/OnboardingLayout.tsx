import { ReactNode } from 'react'
import { usePage } from '@inertiajs/react'
import { Card } from '@heroui/react'
import { Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { FlashMessages } from '@/components/shared/FlashMessages'
import { PageProps } from '@/types/inertia'

const STEP_KEYS = ['email', 'terms', 'profile', 'plan'] as const

interface Props {
  children: ReactNode
  currentStep: number
  title?: string
}

export default function OnboardingLayout({ children, currentStep, title }: Props) {
  const { flash } = usePage<PageProps>().props
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg space-y-8">
        {/* Logo */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-primary">{t('onboarding.brand')}</h1>
          <p className="mt-2 text-sm text-default-500">
            {t('onboarding.subtitle')}
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between px-2">
          {STEP_KEYS.map((key, index) => {
            const step = index + 1
            return (
              <div key={key} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-shrink-0">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                      step < currentStep
                        ? 'bg-primary text-primary-foreground'
                        : step === currentStep
                          ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
                          : 'bg-default-200 text-default-500'
                    }`}
                  >
                    {step < currentStep ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      step
                    )}
                  </div>
                  <span
                    className={`mt-1 text-xs ${
                      step <= currentStep
                        ? 'text-primary font-medium'
                        : 'text-default-400'
                    }`}
                  >
                    {t(`onboarding.steps.${key}`)}
                  </span>
                </div>
                {index < STEP_KEYS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 mt-[-1rem] ${
                      step < currentStep
                        ? 'bg-primary'
                        : 'bg-default-200'
                    }`}
                  />
                )}
              </div>
            )
          })}
        </div>

        {/* Flash messages */}
        <FlashMessages flash={flash} className="" />

        {/* Main Card */}
        <Card className="shadow-xl border border-default-200">
          {title && (
            <Card.Header className="p-6 pb-0">
              <Card.Title className="text-xl font-bold text-foreground">
                {title}
              </Card.Title>
            </Card.Header>
          )}
          <Card.Content className="p-6">
            {children}
          </Card.Content>
        </Card>

        {/* Progress bar */}
        <div className="w-full bg-default-200 rounded-full h-1.5">
          <div
             className="bg-primary h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${(currentStep / STEP_KEYS.length) * 100}%` }}
          />
        </div>
        <p className="text-center text-xs text-default-400">
          {t('onboarding.progress', { current: currentStep, total: STEP_KEYS.length })}
        </p>
      </div>
    </div>
  )
}
