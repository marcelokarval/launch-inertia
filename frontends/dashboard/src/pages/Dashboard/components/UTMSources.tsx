/**
 * UTMSources — Traffic source breakdown.
 */

import { Card } from '@heroui/react';
import { Globe } from 'lucide-react';
import type { UTMSourceItem } from '@/types';

interface Props {
  data: UTMSourceItem[];
}

export function UTMSources({ data }: Props) {
  if (data.length === 0) {
    return (
      <Card className="border border-default-200 animate-fade-in">
        <Card.Header className="pb-0 px-6 pt-6">
          <h2 className="text-lg font-semibold text-foreground">Fontes de Trafego</h2>
        </Card.Header>
        <Card.Content className="p-6">
          <p className="text-sm text-default-400 text-center py-4">Sem dados</p>
        </Card.Content>
      </Card>
    );
  }

  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">Fontes de Trafego</h2>
      </Card.Header>
      <Card.Content className="p-6 space-y-3">
        {data.slice(0, 8).map((item) => {
          const widthPct = Math.max((item.count / maxCount) * 100, 4);
          return (
            <div key={`${item.source}-${item.platform}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Globe className="h-3.5 w-3.5 text-default-400" />
                  <span className="text-sm text-default-700">{item.source}</span>
                  {item.platform !== item.source && (
                    <span className="text-xs text-default-400">{item.platform}</span>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-medium text-foreground">
                    {item.count.toLocaleString('pt-BR')}
                  </span>
                  <span className="text-xs text-default-400">({item.percentage}%)</span>
                </div>
              </div>
              <div className="h-2 rounded-full bg-default-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary/60 transition-all duration-500"
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </Card.Content>
    </Card>
  );
}
