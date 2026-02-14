import { Head, Link } from '@inertiajs/react'
import { Card } from '@heroui/react'
import { Button } from '@/components/ui'
import { CheckCircle, ArrowRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function BillingSuccess() {
  const { t } = useTranslation()

  return (
    <>
      <Head title={t('billing.success.pageTitle')} />

      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md shadow-xl text-center">
          <Card.Content className="p-8">
            <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-success" />
            </div>

            <h1 className="text-2xl font-bold text-foreground mb-2">
              {t('billing.success.title')}
            </h1>

            <p className="text-default-500 mb-8">
              {t('billing.success.description')}
            </p>

            <Link href="/app/">
              <Button variant="primary" fullWidth>
                {t('billing.success.goToDashboard')}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </Card.Content>
        </Card>
      </div>
    </>
  )
}
