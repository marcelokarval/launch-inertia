/**
 * DailyTrendChart — Area chart showing leads + page views over last 30 days.
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
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { DailyTrendPoint } from '@/types';

interface Props {
  data: DailyTrendPoint[];
}

function formatDate(value: unknown): string {
  const d = new Date(String(value) + 'T00:00:00');
  return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
}

export function DailyTrendChart({ data }: Props) {
  const { t } = useTranslation();
  const hasData = data.some((d) => d.leads > 0 || d.page_views > 0);

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
                  <stop offset="5%" stopColor="hsl(var(--heroui-primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--heroui-primary))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientViews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--heroui-default-400))" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="hsl(var(--heroui-default-400))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--heroui-default-200))" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fontSize: 11, fill: 'hsl(var(--heroui-default-500))' }}
                interval="preserveStartEnd"
                tickCount={7}
              />
              <YAxis
                tick={{ fontSize: 11, fill: 'hsl(var(--heroui-default-500))' }}
                width={40}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--heroui-content1))',
                  border: '1px solid hsl(var(--heroui-default-200))',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                labelFormatter={(label) => formatDate(label)}
              />
              <Area
                type="monotone"
                dataKey="page_views"
                name={t('dashboard.analytics.visualizacoes', 'Page Views')}
                stroke="hsl(var(--heroui-default-400))"
                fill="url(#gradientViews)"
                strokeWidth={1.5}
              />
              <Area
                type="monotone"
                dataKey="leads"
                name={t('dashboard.analytics.leads', 'Leads')}
                stroke="hsl(var(--heroui-primary))"
                fill="url(#gradientLeads)"
                strokeWidth={2}
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
