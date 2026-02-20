/**
 * FlashMessages — Shared flash message display using HeroUI Alert.
 *
 * Replaces duplicated raw-div flash patterns across layouts.
 * Uses HeroUI Alert compound component with status prop.
 *
 * Usage:
 *   <FlashMessages flash={flash} />
 *   <FlashMessages flash={flash} className="px-6 pt-4" />
 */

import { Alert } from '@heroui/react';
import { CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react';
import type { PageProps } from '@/types/inertia';

type FlashStatus = 'success' | 'danger' | 'warning' | 'accent';

interface Props {
  flash: PageProps['flash'];
  className?: string;
}

const FLASH_CONFIG: {
  key: keyof PageProps['flash'];
  status: FlashStatus;
  icon: typeof CheckCircle2;
}[] = [
  { key: 'success', status: 'success', icon: CheckCircle2 },
  { key: 'error', status: 'danger', icon: XCircle },
  { key: 'warning', status: 'warning', icon: AlertTriangle },
  { key: 'info', status: 'accent', icon: Info },
];

export function FlashMessages({ flash, className = 'px-6 pt-4' }: Props) {
  if (!flash?.success && !flash?.error && !flash?.warning && !flash?.info) {
    return null;
  }

  return (
    <div className={`${className} space-y-2`}>
      {FLASH_CONFIG.map(({ key, status, icon: Icon }) => {
        const message = flash[key];
        if (!message) return null;

        return (
          <Alert key={key} status={status} className="animate-slide-up">
            <Alert.Indicator>
              <Icon className="h-4 w-4" />
            </Alert.Indicator>
            <Alert.Content>
              <Alert.Description>{message}</Alert.Description>
            </Alert.Content>
          </Alert>
        );
      })}
    </div>
  );
}
