/**
 * Dashboard Index — Real Analytics
 *
 * Displays capture funnel metrics, daily trends, top pages,
 * device breakdown, UTM sources, and recent captures.
 * All data from AnalyticsService via Inertia props.
 */

import { Head } from '@inertiajs/react';
import { useTranslation } from 'react-i18next';
import DashboardLayout from '@/layouts/DashboardLayout';
import { StatCards } from './components/StatCards';
import { DailyTrendChart } from './components/DailyTrendChart';
import { FunnelChart } from './components/FunnelChart';
import { TopPagesTable } from './components/TopPagesTable';
import { DeviceBreakdown } from './components/DeviceBreakdown';
import { RecentCaptures } from './components/RecentCaptures';
import { UTMSources } from './components/UTMSources';
import type { AnalyticsData, SharedUser } from '@/types';

// ============================================================================
// Types
// ============================================================================

interface Props {
  user: SharedUser;
  analytics: AnalyticsData;
  unread_notifications: number;
}

// ============================================================================
// Main Component
// ============================================================================

export default function DashboardIndex({ user, analytics }: Props) {
  const { t } = useTranslation();

  const { overview, daily_trend, funnel, top_pages, device_breakdown, utm_sources, recent_captures } = analytics;

  return (
    <DashboardLayout title={t('dashboard.title')}>
      <Head title={t('dashboard.pageTitle')} />

      {/* Welcome */}
      <div className="mb-2">
        <h1 className="text-3xl font-bold text-foreground mb-1">
          {t('dashboard.welcome', { name: user.name })}
        </h1>
        <p className="text-default-500">
          {t('dashboard.subtitle', "Here's an overview of your launch activity.")}
        </p>
      </div>

      {/* Stat Cards */}
      <StatCards overview={overview} />

      {/* Charts Row: Trend + Funnel */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
        <div className="lg:col-span-4">
          <DailyTrendChart data={daily_trend} />
        </div>
        <div className="lg:col-span-3">
          <FunnelChart funnel={funnel} />
        </div>
      </div>

      {/* Top Pages */}
      {top_pages.length > 0 && <TopPagesTable pages={top_pages} />}

      {/* Bottom Row: Devices + UTM + Recent */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DeviceBreakdown data={device_breakdown} />
        <UTMSources data={utm_sources} />
        <RecentCaptures captures={recent_captures} />
      </div>
    </DashboardLayout>
  );
}
