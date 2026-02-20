import { router } from '@inertiajs/react';
import { Avatar } from '@heroui/react';
import { Button } from '@/components/ui';
import { Plus, Shield } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function EmptyState() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Avatar size="lg" className="mb-4 bg-default-100">
        <Avatar.Fallback>
          <Shield className="w-8 h-8 text-default-300" />
        </Avatar.Fallback>
      </Avatar>
      <h3 className="text-lg font-semibold text-foreground mb-1">
        {t('identities.index.emptyTitle', 'No identities yet')}
      </h3>
      <p className="text-sm text-default-500 mb-4 text-center max-w-sm">
        {t('identities.index.emptyDesc', 'Start by importing your first identity to begin resolution.')}
      </p>
      <Button
        variant="primary"
        onPress={() => router.visit('/app/identities/create/')}
      >
        <Plus className="w-4 h-4" />
        {t('identities.index.addFirst', 'Import your first identity')}
      </Button>
    </div>
  );
}
