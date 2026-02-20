/**
 * TopPagesTable — Table of top capture pages by conversions.
 */

import { Card, Chip } from '@heroui/react';
import { useTranslation } from 'react-i18next';
import type { CapturePageStats } from '@/types';

interface Props {
  pages: CapturePageStats[];
}

function rateColor(rate: number): 'success' | 'warning' | 'danger' | 'default' {
  if (rate >= 10) return 'success';
  if (rate >= 5) return 'warning';
  if (rate > 0) return 'danger';
  return 'default';
}

export function TopPagesTable({ pages }: Props) {
  const { t } = useTranslation();

  return (
    <Card className="border border-default-200 animate-fade-in">
      <Card.Header className="pb-0 px-6 pt-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t('dashboard.analytics.topPaginasCaptura', 'Top Paginas de Captura')}
        </h2>
      </Card.Header>
      <Card.Content className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-default-200">
                <th className="text-left py-3 px-2 font-medium text-default-500">
                  {t('dashboard.analytics.pagina', 'Pagina')}
                </th>
                <th className="text-left py-3 px-2 font-medium text-default-500">
                  {t('dashboard.analytics.lancamento', 'Lancamento')}
                </th>
                <th className="text-right py-3 px-2 font-medium text-default-500">
                  Views
                </th>
                <th className="text-right py-3 px-2 font-medium text-default-500">
                  Leads
                </th>
                <th className="text-right py-3 px-2 font-medium text-default-500">
                  {t('dashboard.analytics.conversao', 'Conversao')}
                </th>
              </tr>
            </thead>
            <tbody>
              {pages.map((page) => (
                <tr key={page.slug} className="border-b border-default-100 hover:bg-default-50 transition-colors">
                  <td className="py-3 px-2">
                    <div>
                      <p className="font-medium text-foreground">{page.name}</p>
                      <p className="text-xs text-default-400">/{page.slug}/</p>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-default-600">{page.launch_name || '--'}</td>
                  <td className="py-3 px-2 text-right text-default-600">
                    {page.page_views.toLocaleString('pt-BR')}
                  </td>
                  <td className="py-3 px-2 text-right font-medium text-foreground">
                    {page.submissions.toLocaleString('pt-BR')}
                  </td>
                  <td className="py-3 px-2 text-right">
                    <Chip variant="soft" color={rateColor(page.conversion_rate)} size="sm">
                      {page.conversion_rate}%
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card.Content>
    </Card>
  );
}
