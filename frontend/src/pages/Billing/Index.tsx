import { Head, router } from '@inertiajs/react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { Card, Chip, Link as HeroLink } from '@heroui/react'
import { Button } from '@/components/ui'
import { CreditCard, Receipt, ExternalLink, AlertCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Subscription, Invoice } from '@/types'

interface Props {
  subscription?: Subscription | null
  invoices: Invoice[]
}

export default function BillingIndex({ subscription, invoices }: Props) {
  const { t } = useTranslation()

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(amount / 100)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR')
  }

  const openPortal = () => {
    router.post('/billing/portal/', {}, { forceFormData: true })
  }

  return (
    <DashboardLayout title={t('billing.index.title')}>
      <Head title={t('billing.index.pageTitle')} />

      <div className="max-w-4xl mx-auto space-y-6">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-foreground">
            {t('billing.index.title')}
          </h2>
          <p className="mt-1 text-default-500">
            {t('billing.index.description')}
          </p>
        </div>

        {/* Current Subscription */}
        <Card>
          <Card.Header className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CreditCard className="w-6 h-6 text-primary" />
                <Card.Title>{t('billing.index.subscription.title')}</Card.Title>
              </div>
              {subscription && (
                <Chip
                  color={subscription.status === 'active' ? 'success' : 'warning'}
                  variant="soft"
                >
                  {subscription.status === 'active' ? t('billing.index.subscription.active') : subscription.status}
                </Chip>
              )}
            </div>
          </Card.Header>
          <Card.Content className="p-6 pt-0">
            {subscription ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-default-500">{t('billing.index.subscription.planLabel')}</p>
                  <p className="font-semibold text-foreground">
                    {subscription.plan_name || t('billing.index.subscription.defaultPlan')}
                  </p>
                </div>
                {subscription.current_period_end && (
                  <div>
                    <p className="text-sm text-default-500">{t('billing.index.subscription.nextBilling')}</p>
                    <p className="font-semibold text-foreground">
                      {formatDate(subscription.current_period_end)}
                    </p>
                  </div>
                )}
                <div className="pt-4">
                  <Button
                    onPress={openPortal}
                    variant="primary"
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    {t('billing.index.subscription.manage')}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-default-400 mx-auto mb-4" />
                <p className="text-default-500 mb-4">
                  {t('billing.index.noSubscription')}
                </p>
                <Button variant="primary">
                  {t('billing.index.choosePlan')}
                </Button>
              </div>
            )}
          </Card.Content>
        </Card>

        {/* Invoices */}
        <Card>
          <Card.Header className="p-6">
            <div className="flex items-center gap-3">
              <Receipt className="w-6 h-6 text-primary" />
              <Card.Title>{t('billing.index.invoices.title')}</Card.Title>
            </div>
          </Card.Header>
          <Card.Content className="p-6 pt-0">
            {invoices.length > 0 ? (
              <div className="space-y-4">
                {invoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-default-200"
                  >
                    <div>
                      <p className="font-medium text-foreground">
                        {formatCurrency(invoice.amount_due)}
                      </p>
                      <p className="text-sm text-default-500">
                        {formatDate(invoice.created)}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <Chip
                        color={invoice.status === 'paid' ? 'success' : 'warning'}
                        variant="soft"
                      >
                        {invoice.status === 'paid' ? t('billing.index.invoices.paid') : invoice.status}
                      </Chip>
                      {invoice.invoice_pdf && (
                        <HeroLink
                          href={invoice.invoice_pdf}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:opacity-80"
                        >
                          <ExternalLink className="w-5 h-5" />
                        </HeroLink>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-default-500 py-8">
                {t('billing.index.invoices.empty')}
              </p>
            )}
          </Card.Content>
        </Card>
      </div>
    </DashboardLayout>
  )
}
