import { Head } from '@inertiajs/react';

import CaptureLayout from '@/layouts/CaptureLayout';
import type { ThankYouPageProps } from '@/types';

/**
 * ThankYou/Index — Post-capture confirmation page.
 *
 * Minimal placeholder for Phase D. Full implementation in Phase F
 * (CPL video, WhatsApp group link, etc.).
 */
export default function ThankYouIndex({ campaign }: ThankYouPageProps) {
  return (
    <CaptureLayout>
      <Head title={`Obrigado - ${campaign.meta.title}`} />

      <div className="rounded-2xl bg-[var(--color-surface)] p-6 text-center shadow-2xl sm:p-8">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-success)]/10">
          <svg
            className="h-8 w-8 text-[var(--color-success)]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>

        <h1 className="mb-2 text-2xl font-bold text-[var(--color-text-primary)]">
          Inscricao confirmada!
        </h1>

        <p className="text-[var(--color-text-secondary)]">
          Obrigado pelo seu interesse. Fique de olho no seu e-mail
          e WhatsApp para mais informacoes.
        </p>
      </div>
    </CaptureLayout>
  );
}
