/**
 * StatCards — 4 overview metrics at the top of the dashboard.
 */

import { Card } from '@heroui/react';
import {
  Users,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Eye,
  Rocket,
} from 'lucide-react';
import type { ComponentType } from 'react';
import type { AnalyticsOverview } from '@/types';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ComponentType<{ className?: string }>;
  trend?: { value: string; positive: boolean };
  variant?: 'default' | 'gradient';
}

function StatCard({ title, value, icon: Icon, trend, variant = 'default' }: StatCardProps) {
  const isGradient = variant === 'gradient';

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
              vs semana anterior
            </span>
          </div>
        )}
      </Card.Content>
    </Card>
  );
}

interface Props {
  overview: AnalyticsOverview;
}

export function StatCards({ overview }: Props) {
  const cards: StatCardProps[] = [
    {
      title: 'Leads Capturados',
      value: overview.total_leads.toLocaleString('pt-BR'),
      icon: Users,
      variant: 'gradient',
      trend:
        overview.leads_this_week > 0
          ? {
              value: `${overview.wow_growth > 0 ? '+' : ''}${overview.wow_growth}%`,
              positive: overview.wow_growth >= 0,
            }
          : undefined,
    },
    {
      title: 'Taxa de Conversao',
      value: `${overview.conversion_rate}%`,
      icon: TrendingUp,
    },
    {
      title: 'Visualizacoes',
      value: overview.total_page_views.toLocaleString('pt-BR'),
      icon: Eye,
    },
    {
      title: 'Lancamentos Ativos',
      value: overview.active_launches.toLocaleString('pt-BR'),
      icon: Rocket,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, i) => (
        <StatCard key={i} {...card} />
      ))}
    </div>
  );
}
