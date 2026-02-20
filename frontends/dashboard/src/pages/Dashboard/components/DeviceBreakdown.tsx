/**
 * DeviceBreakdown — Pie-style breakdown of desktop/mobile/tablet.
 */

import { Card } from '@heroui/react';
import { Monitor, Smartphone, Tablet, HelpCircle } from 'lucide-react';
import type { DeviceBreakdownItem } from '@/types';

interface Props {
  data: DeviceBreakdownItem[];
}

const DEVICE_ICONS: Record<string, typeof Monitor> = {
  desktop: Monitor,
  mobile: Smartphone,
  tablet: Tablet,
};

const DEVICE_COLORS: Record<string, string> = {
  desktop: 'bg-primary',
  mobile: 'bg-secondary',
  tablet: 'bg-warning',
};

export function DeviceBreakdown({ data }: Props) {
  if (data.length === 0) {
    return (
      <Card className="border border-default-200 animate-fade-in">
        <Card.Header className="pb-0 px-6 pt-6">
          <h2 className="text-lg font-semibold text-foreground">Dispositivos</h2>
        </Card.Header>
        <Card.Content className="p-6">
          <p className="text-sm text-default-400 text-center py-4">Sem dados</p>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">Dispositivos</h2>
      </Card.Header>
      <Card.Content className="p-6 space-y-4">
        {/* Stacked bar */}
        <div className="h-4 rounded-full overflow-hidden flex bg-default-100">
          {data.map((item) => (
            <div
              key={item.device_type}
              className={`h-full ${DEVICE_COLORS[item.device_type] || 'bg-default-300'} transition-all duration-500`}
              style={{ width: `${item.percentage}%` }}
            />
          ))}
        </div>

        {/* Legend */}
        <div className="space-y-3">
          {data.map((item) => {
            const Icon = DEVICE_ICONS[item.device_type] || HelpCircle;
            return (
              <div key={item.device_type} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${DEVICE_COLORS[item.device_type] || 'bg-default-300'}`} />
                  <Icon className="h-4 w-4 text-default-500" />
                  <span className="text-sm text-default-700 capitalize">{item.device_type}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">
                    {item.count.toLocaleString('pt-BR')}
                  </span>
                  <span className="text-xs text-default-400">({item.percentage}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      </Card.Content>
    </Card>
  );
}
