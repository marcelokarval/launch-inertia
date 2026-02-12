/**
 * Onboarding Step 4: Plan Selection
 */

import { useState } from 'react'
import { Head } from '@inertiajs/react'
import { Card, Chip, Form, RadioGroup, Radio } from '@heroui/react'
import { Button, FormErrorBanner } from '@/components/ui'
import { Check, Zap, Star, Crown } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import OnboardingLayout from '@/layouts/OnboardingLayout'
import { useAppForm } from '@/hooks/useAppForm'
import type { Plan } from '@/types'

interface Props {
  plans?: Plan[]
  errors?: Record<string, string[]>
}

const PLAN_ICONS: Record<string, typeof Zap> = {
  free: Zap,
  basic: Star,
  premium: Crown,
}

const PLAN_COLORS: Record<string, { bg: string; border: string; badge: string }> = {
  free: {
    bg: 'bg-default-50',
    border: 'border-default-200',
    badge: 'bg-default-100 text-default-700',
  },
  basic: {
    bg: 'bg-primary/5',
    border: 'border-primary/20',
    badge: 'bg-primary/10 text-primary',
  },
  premium: {
    bg: 'bg-secondary/5',
    border: 'border-secondary/20',
    badge: 'bg-secondary/10 text-secondary',
  },
}

export default function PlanSelection({ plans = [], errors = {} }: Props) {
  const { t } = useTranslation()
  const [selectedPlan, setSelectedPlan] = useState('free')

  const { submit, isSubmitting, setData } = useAppForm({
    initialData: {
      plan: 'free',
    },
    url: '/onboarding/plan-selection/',
    method: 'post',
  })

  function handleSelectPlan(planId: string) {
    setSelectedPlan(planId)
    setData('plan', planId)
  }

  const planError = errors.plan?.[0]

  return (
    <OnboardingLayout currentStep={4} title={t('onboarding.plan.title')}>
      <Head title={t('onboarding.plan.pageTitle')} />

      <div className="space-y-6">
        <p className="text-sm text-default-600">
          {t('onboarding.plan.instruction')}
        </p>

        {/* Error */}
        <FormErrorBanner message={planError} />

        <Form onSubmit={submit} className="space-y-4">
          {/* Plan Cards */}
          <RadioGroup
            value={selectedPlan}
            onChange={(value) => handleSelectPlan(value)}
            className="space-y-3"
          >
            {plans.map((plan) => {
              const isSelected = selectedPlan === plan.id
              const Icon = PLAN_ICONS[plan.id] || Zap
              const colors = PLAN_COLORS[plan.id] || PLAN_COLORS.free

              return (
                <Radio key={plan.id} value={plan.id} className="w-full">
                  <Radio.Control />
                  <Radio.Content>
                    <Card
                      className={`cursor-pointer transition-all duration-200 w-full ${
                        isSelected
                          ? `ring-2 ring-primary ${colors.bg} ${colors.border}`
                          : `hover:shadow-md border ${colors.border} ${colors.bg}`
                      }`}
                    >
                      <Card.Content className="p-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Icon className="w-4 h-4 text-primary" />
                              <h3 className="font-semibold text-foreground">
                                {plan.name}
                              </h3>
                              {plan.id === 'basic' && (
                                <Chip size="sm" variant="soft" color="accent">
                                  {t('onboarding.plan.popular')}
                                </Chip>
                              )}
                            </div>
                            <div className="text-right">
                              {(plan.price ?? plan.amount) === 0 ? (
                                <span className="text-lg font-bold text-foreground">
                                  {t('onboarding.plan.free')}
                                </span>
                              ) : (
                                <div>
                                  <span className="text-lg font-bold text-foreground">
                                    ${plan.price ?? plan.amount}
                                  </span>
                                  <span className="text-xs text-default-500">{t('onboarding.plan.pricePerMonth')}</span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Features */}
                          <ul className="mt-2 space-y-1">
                            {(plan.features ?? []).map((feature, idx) => (
                              <li
                                key={idx}
                                className="flex items-center gap-2 text-xs text-default-600"
                              >
                                <Check className="w-3.5 h-3.5 text-success flex-shrink-0" />
                                {feature}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </Card.Content>
                    </Card>
                  </Radio.Content>
                </Radio>
              )
            })}
          </RadioGroup>

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={isSubmitting}
            loadingText={t('onboarding.plan.submitting')}
          >
            {selectedPlan === 'free'
              ? t('onboarding.plan.submitFree')
              : t('onboarding.plan.submitPlan', { name: plans.find((p) => p.id === selectedPlan)?.name || 'Selected' })}
          </Button>

          <p className="text-center text-xs text-default-400">
            {t('onboarding.plan.footer')}
          </p>
        </Form>
      </div>
    </OnboardingLayout>
  )
}
