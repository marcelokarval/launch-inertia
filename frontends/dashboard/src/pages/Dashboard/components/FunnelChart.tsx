/**
 * FunnelChart — Horizontal bar funnel: page_view -> intent -> attempt -> success.
 */

import { Card } from '@heroui/react';
import { useTranslation } from 'react-i18next';
import type { FunnelMetrics } from '@/types';

interface Props {
  funnel: FunnelMetrics;
}

const STAGE_COLORS = [
  'bg-default-300',
  'bg-warning',
  'bg-secondary',
  'bg-primary',
];

export function FunnelChart({ funnel }: Props) {
  const { t } = useTranslation();
  const maxCount = Math.max(...funnel.stages.map((s) => s.count), 1);

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <div className="flex items-center justify-between w-full">
          <h2 className="text-lg font-semibold text-foreground">
            {t('dashboard.analytics.funilCaptura', 'Capture Funnel')}
          </h2>
          <span className="text-sm text-default-500">
            {t('dashboard.analytics.conversao', 'Conversion')}:{' '}
            <span className="font-semibold text-primary">{funnel.overall_conversion}%</span>
          </span>
        </div>
      </Card.Header>
      <Card.Content className="p-6 space-y-4">
        {funnel.stages.map((stage, i) => {
          const widthPct = maxCount > 0 ? Math.max((stage.count / maxCount) * 100, 4) : 4;

          return (
            <div key={stage.name}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-default-700">{stage.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">
                    {stage.count.toLocaleString()}
                  </span>
                  {i > 0 && (
                    <span className="text-xs text-default-400">({stage.rate}%)</span>
                  )}
                </div>
              </div>
              <div className="h-6 rounded-lg bg-default-100 overflow-hidden">
                <div
                  className={`h-full rounded-lg ${STAGE_COLORS[i]} transition-all duration-500`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}

        {funnel.form_errors > 0 && (
          <div className="pt-2 border-t border-default-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-danger-500">
                {t('dashboard.analytics.errosFormulario', 'Form errors')}
              </span>
              <span className="font-medium text-danger-600">
                {funnel.form_errors.toLocaleString()} ({funnel.error_rate}%)
              </span>
            </div>
          </div>
        )}
      </Card.Content>
    </Card>
  );
}
