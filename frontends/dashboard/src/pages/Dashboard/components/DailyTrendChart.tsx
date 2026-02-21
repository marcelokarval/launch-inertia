/**
 * DailyTrendChart — Area chart showing leads + page views over last 30 days.
 *
 * Uses inline style colors (not CSS vars) for Recharts compatibility.
 * Recharts SVG elements don't resolve CSS custom properties reliably
 * across theme changes, so we use fixed colors with good contrast in both modes.
 */

import { Card } from '@heroui/react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { DailyTrendPoint } from '@/types';

/** Fixed colors that work in both light and dark themes. */
const COLORS = {
  leads: '#7c3aed',       // vivid purple — always visible
  pageViews: '#6b7280',   // neutral gray-500 — good in both
  unique: '#10b981',      // emerald-500 — good in both
  grid: '#d1d5db',        // gray-300
  tick: '#9ca3af',        // gray-400
} as const;

interface Props {
  data: DailyTrendPoint[];
}

function formatDate(value: unknown): string {
  const d = new Date(String(value) + 'T00:00:00');
  return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
}

export function DailyTrendChart({ data }: Props) {
  const { t } = useTranslation();
  const hasData = data.some((d) => d.leads > 0 || d.page_views > 0 || d.unique_visitors > 0);

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t('dashboard.analytics.capturasDiarias', 'Daily Captures')}
        </h2>
      </Card.Header>
      <Card.Content className="p-6">
        {hasData ? (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradientLeads" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.leads} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.leads} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientViews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.pageViews} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={COLORS.pageViews} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientUnique" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.unique} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={COLORS.unique} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} strokeOpacity={0.4} />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fontSize: 11, fill: COLORS.tick }}
                interval="preserveStartEnd"
                tickCount={7}
              />
              <YAxis
                tick={{ fontSize: 11, fill: COLORS.tick }}
                width={40}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--heroui-content1))',
                  border: '1px solid hsl(var(--heroui-default-200))',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: 'hsl(var(--heroui-foreground))',
                }}
                labelStyle={{ color: 'hsl(var(--heroui-foreground))' }}
                itemStyle={{ color: 'hsl(var(--heroui-foreground))' }}
                labelFormatter={(label) => formatDate(label)}
              />
              <Legend
                wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }}
              />
              <Area
                type="monotone"
                dataKey="page_views"
                name={t('dashboard.analytics.visualizacoes', 'Page Views')}
                stroke={COLORS.pageViews}
                fill="url(#gradientViews)"
                strokeWidth={1.5}
              />
              <Area
                type="monotone"
                dataKey="unique_visitors"
                name={t('dashboard.analytics.visitantesUnicos', 'Unique Visitors')}
                stroke={COLORS.unique}
                fill="url(#gradientUnique)"
                strokeWidth={1.5}
                strokeDasharray="4 2"
              />
              <Area
                type="monotone"
                dataKey="leads"
                name={t('dashboard.analytics.leads', 'Leads')}
                stroke={COLORS.leads}
                fill="url(#gradientLeads)"
                strokeWidth={2.5}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[280px] flex items-center justify-center">
            <p className="text-default-400 text-sm">
              {t('dashboard.analytics.nenhumDadoCaptura', 'No capture data yet')}
            </p>
          </div>
        )}
      </Card.Content>
    </Card>
  );
}
