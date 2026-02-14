/**
 * Dashboard Index - HeroUI v3 Native
 *
 * Based on dashboard-react-para-launch design.
 * Gradient stat card, quick actions, activity feed, system status.
 */

import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Card } from '@heroui/react'
import { Button } from '@/components/ui'
import DashboardLayout from '@/layouts/DashboardLayout'
import {
  Users,
  CreditCard,
  TrendingUp,
  TrendingDown,
  Plus,
  Target,
  DollarSign,
  Activity,
  Settings,
  ArrowUpRight,
  Rocket,
} from 'lucide-react'
import type { ComponentType } from 'react'
import type { DashboardStats, SharedUser } from '@/types'

// ============================================================================
// Types
// ============================================================================

interface Props {
  user: SharedUser
  stats?: DashboardStats
}

// ============================================================================
// Stat Card
// ============================================================================

interface StatCardProps {
  title: string
  value: string | number
  icon: ComponentType<{ className?: string }>
  trend?: { value: string; positive: boolean }
  variant?: 'default' | 'gradient'
}

function StatCard({ title, value, icon: Icon, trend, variant = 'default' }: StatCardProps) {
  const isGradient = variant === 'gradient'

  return (
    <Card
      className={`border transition-all duration-200 animate-fade-in ${
        isGradient
          ? 'bg-gradient-primary text-white border-transparent shadow-lg shadow-brand'
          : 'border-default-200 hover:shadow-md hover:border-default-300'
      }`}
    >
      <Card.Content className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className={`text-sm mb-1 ${isGradient ? 'text-background/80' : 'text-default-500'}`}>
              {title}
            </p>
            <p className={`text-3xl font-bold ${isGradient ? 'text-white' : 'text-foreground'}`}>
              {value}
            </p>
          </div>
          <div className={`p-3 rounded-xl ${isGradient ? 'bg-background/20' : 'bg-primary/10'}`}>
            <Icon className={`h-6 w-6 ${isGradient ? 'text-white' : 'text-primary'}`} />
          </div>
        </div>
        {trend && (
          <div className="flex items-center gap-1.5 mt-3">
            {trend.positive ? (
              <ArrowUpRight className={`h-4 w-4 ${isGradient ? 'text-background/90' : 'text-success'}`} />
            ) : (
              <TrendingDown className={`h-4 w-4 ${isGradient ? 'text-background/90' : 'text-danger'}`} />
            )}
            <span className={`text-sm font-medium ${isGradient ? 'text-background/90' : trend.positive ? 'text-success' : 'text-danger'}`}>
              {trend.value}
            </span>
            <span className={`text-xs ${isGradient ? 'text-background/60' : 'text-default-400'}`}>
              vs last month
            </span>
          </div>
        )}
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// Quick Actions
// ============================================================================

function QuickActionsCard() {
  const { t } = useTranslation()

  const actions = [
    { href: '/app/identities/create/', icon: Plus, label: t('dashboard.quickActions.importIdentity', 'Import Identity'), color: 'text-primary' },
    { href: '#', icon: Target, label: t('dashboard.quickActions.newCampaign', 'New Campaign'), color: 'text-warning' },
    { href: '/app/billing/', icon: CreditCard, label: t('dashboard.quickActions.manageBilling', 'Billing'), color: 'text-success' },
    { href: '/app/settings/', icon: Settings, label: t('dashboard.quickActions.viewSettings', 'Settings'), color: 'text-default-500' },
  ]

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t('dashboard.quickActions.title', 'Quick Actions')}
        </h2>
      </Card.Header>
      <Card.Content className="p-6 space-y-2">
        {actions.map((action) => (
          <Link key={action.label} href={action.href} className="block">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl border-2 border-dashed border-default-200 hover:border-primary/40 hover:bg-primary/5 transition-all duration-200 cursor-pointer group">
              <div className="p-2 rounded-lg bg-default-100 group-hover:bg-primary/10 transition-colors">
                <action.icon className={`h-4 w-4 ${action.color} group-hover:text-primary transition-colors`} />
              </div>
              <span className="text-sm font-medium text-default-700 group-hover:text-foreground transition-colors">
                {action.label}
              </span>
            </div>
          </Link>
        ))}
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// Recent Activity
// ============================================================================

function RecentActivityCard() {
  const { t } = useTranslation()

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <div className="flex items-center justify-between w-full">
          <h2 className="text-lg font-semibold text-foreground">
            {t('dashboard.recentActivity.title', 'Recent Activity')}
          </h2>
          <Link href="/app/notifications/">
            <Button variant="ghost" size="sm">
              {t('dashboard.recentActivity.viewAll', 'View All')}
            </Button>
          </Link>
        </div>
      </Card.Header>
      <Card.Content className="p-6">
        <div className="text-center py-8">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-default-100 flex items-center justify-center mb-4">
            <Activity className="h-8 w-8 text-default-300" />
          </div>
          <p className="text-default-500 font-medium">
            {t('dashboard.recentActivity.empty', 'No recent activity')}
          </p>
          <p className="text-sm text-default-400 mt-1">
            {t('dashboard.recentActivity.emptyDescription', 'Your activity will appear here as you use the platform')}
          </p>
        </div>
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// Sales Overview (placeholder)
// ============================================================================

function SalesOverviewCard() {
  const { t } = useTranslation()

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t('dashboard.salesOverview.title', 'Sales Overview')}
        </h2>
      </Card.Header>
      <Card.Content className="p-6">
        <div className="h-48 rounded-xl bg-gradient-to-br from-primary/5 to-secondary/5 border-2 border-dashed border-default-200 flex items-center justify-center">
          <div className="text-center">
            <Activity className="h-10 w-10 text-default-300 mx-auto mb-2" />
            <p className="text-sm text-default-400">Charts coming soon</p>
          </div>
        </div>
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// System Status
// ============================================================================

function SystemStatusCard() {
  const { t } = useTranslation()

  const systems = [
    { name: 'API', status: 'operational' },
    { name: 'Email Service', status: 'operational' },
    { name: 'Background Jobs', status: 'operational' },
  ]

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t('dashboard.systemStatus.title', 'System Status')}
        </h2>
      </Card.Header>
      <Card.Content className="p-6 space-y-4">
        {systems.map((sys) => (
          <div key={sys.name} className="flex items-center justify-between">
            <span className="text-sm text-default-600">{sys.name}</span>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-success font-medium capitalize">{sys.status}</span>
            </div>
          </div>
        ))}
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// Getting Started CTA
// ============================================================================

function GettingStartedCard() {
  const { t } = useTranslation()

  return (
    <Card className="border border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10 animate-slide-up">
      <Card.Content className="p-6">
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="p-4 rounded-2xl bg-gradient-primary flex-shrink-0 shadow-lg shadow-brand">
            <Rocket className="h-8 w-8 text-white" />
          </div>
          <div className="flex-1 text-center sm:text-left">
            <h3 className="text-lg font-semibold text-foreground mb-1">
              {t('dashboard.gettingStarted.title', 'Get Started with Launch')}
            </h3>
            <p className="text-default-500 text-sm">
              {t('dashboard.gettingStarted.description', 'Import your first identity to start managing your launch campaigns.')}
            </p>
          </div>
          <Link href="/app/identities/create/" className="flex-shrink-0">
            <Button variant="primary" size="lg">
              <Plus className="h-4 w-4" />
              {t('dashboard.gettingStarted.cta', 'Import First Identity')}
            </Button>
          </Link>
        </div>
      </Card.Content>
    </Card>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export default function DashboardIndex({ user, stats }: Props) {
  const { t } = useTranslation()

  const totalIdentities = stats?.total_identities ?? 0
  const activeSubscriptions = stats?.active_subscriptions ?? 0
  const unreadNotifications = stats?.unread_notifications ?? 0
  const conversionRate = stats?.conversion_rate ?? 0

  const statCards: StatCardProps[] = [
    {
      title: t('dashboard.stats.totalIdentities', 'Active Campaigns'),
      value: totalIdentities.toLocaleString(),
      icon: Target,
      variant: 'gradient',
    },
    {
      title: t('dashboard.stats.activeSubscriptions', 'Leads Captured'),
      value: activeSubscriptions.toLocaleString(),
      icon: Users,
      trend: activeSubscriptions > 0 ? { value: '+24%', positive: true } : undefined,
    },
    {
      title: t('dashboard.stats.conversionRate', 'Conversion Rate'),
      value: `${conversionRate}%`,
      icon: TrendingUp,
      trend: conversionRate > 0 ? { value: `+${conversionRate}%`, positive: true } : undefined,
    },
    {
      title: t('dashboard.stats.unreadNotifications', 'Revenue'),
      value: unreadNotifications > 0 ? `$${unreadNotifications.toLocaleString()}` : '--',
      icon: DollarSign,
    },
  ]

  return (
    <DashboardLayout title={t('dashboard.title')}>
      <Head title={t('dashboard.pageTitle')} />

      {/* Welcome */}
      <div className="mb-2">
        <h1 className="text-3xl font-bold text-foreground mb-1">
          {t('dashboard.welcome', { name: user.name })} 👋
        </h1>
        <p className="text-default-500">
          {t('dashboard.subtitle', 'Here\'s an overview of your launch activity today.')}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, i) => (
          <StatCard key={i} {...card} />
        ))}
      </div>

      {/* Main content: 7-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
        {/* Left column (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <QuickActionsCard />
          <SalesOverviewCard />
        </div>

        {/* Right column (3 cols) */}
        <div className="lg:col-span-3 space-y-6">
          <RecentActivityCard />
          <SystemStatusCard />
        </div>
      </div>

      {/* Getting Started (new users) */}
      {totalIdentities === 0 && <GettingStartedCard />}
    </DashboardLayout>
  )
}
