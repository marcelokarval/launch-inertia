/**
 * Onboarding Step 2: Legal Agreements (Terms + Privacy)
 */

import { Head } from '@inertiajs/react'
import { Card, Checkbox, Form, Link as HeroLink } from '@heroui/react'
import { Button, FormErrorBanner } from '@/components/ui'
import { FileText, Shield, Mail } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import OnboardingLayout from '@/layouts/OnboardingLayout'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  errors?: Record<string, string[]>
}

export default function Legal({ errors = {} }: Props) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      agreed_to_terms: false as boolean,
      agreed_to_privacy: false as boolean,
      agreed_to_marketing: false as boolean,
    },
    url: '/onboarding/legal/',
    method: 'post',
  })

  const termsError = errors.terms?.[0]
  const canSubmit = data.agreed_to_terms && data.agreed_to_privacy

  return (
    <OnboardingLayout currentStep={2} title={t('onboarding.legal.title')}>
      <Head title={t('onboarding.legal.pageTitle')} />

      <div className="space-y-6">
        <p className="text-sm text-default-600">
          {t('onboarding.legal.instruction')}
        </p>

        <Form onSubmit={submit} className="space-y-6">
          {/* Terms of Use */}
          <Card className="border border-default-200">
            <Card.Content className="p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
                  <FileText className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1 space-y-1">
                  <h3 className="text-sm font-semibold text-foreground">
                    {t('onboarding.legal.termsTitle')}
                  </h3>
                  <p className="text-xs text-default-500">
                    {t('onboarding.legal.termsDescription')}
                  </p>
                  <HeroLink
                    href="#"
                    className="text-xs text-primary hover:opacity-80"
                  >
                    {t('onboarding.legal.readTerms')}
                  </HeroLink>
                </div>
              </div>
              <Checkbox
                isSelected={data.agreed_to_terms}
                onChange={(isSelected) => setData('agreed_to_terms', isSelected)}
              >
                <span className="text-sm text-default-700">
                  {t('onboarding.legal.agreeTerms')} <span className="text-danger">*</span>
                </span>
              </Checkbox>
            </Card.Content>
          </Card>

          {/* Privacy Policy */}
          <Card className="border border-default-200">
            <Card.Content className="p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-success/10 flex-shrink-0">
                  <Shield className="w-4 h-4 text-success" />
                </div>
                <div className="flex-1 space-y-1">
                  <h3 className="text-sm font-semibold text-foreground">
                    {t('onboarding.legal.privacyTitle')}
                  </h3>
                  <p className="text-xs text-default-500">
                    {t('onboarding.legal.privacyDescription')}
                  </p>
                  <HeroLink
                    href="#"
                    className="text-xs text-primary hover:opacity-80"
                  >
                    {t('onboarding.legal.readPrivacy')}
                  </HeroLink>
                </div>
              </div>
              <Checkbox
                isSelected={data.agreed_to_privacy}
                onChange={(isSelected) => setData('agreed_to_privacy', isSelected)}
              >
                <span className="text-sm text-default-700">
                  {t('onboarding.legal.agreePrivacy')} <span className="text-danger">*</span>
                </span>
              </Checkbox>
            </Card.Content>
          </Card>

          {/* Marketing (Optional) */}
          <Card className="border border-default-100 bg-default-50">
            <Card.Content className="p-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-secondary/10 flex-shrink-0">
                  <Mail className="w-4 h-4 text-secondary" />
                </div>
                <div className="flex-1">
                  <Checkbox
                    isSelected={data.agreed_to_marketing}
                    onChange={(isSelected) => setData('agreed_to_marketing', isSelected)}
                  >
                    <span className="text-sm text-default-700">
                      {t('onboarding.legal.marketingLabel')}
                    </span>
                  </Checkbox>
                  <p className="text-xs text-default-400 mt-1 ml-6">
                    {t('onboarding.legal.marketingHelp')}
                  </p>
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Error */}
          <FormErrorBanner message={termsError} />

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={isSubmitting}
            loadingText={t('onboarding.legal.submitting')}
            isDisabled={!canSubmit}
          >
            {t('onboarding.legal.submit')}
          </Button>
        </Form>
      </div>
    </OnboardingLayout>
  )
}
