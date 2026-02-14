import { Head, Link } from '@inertiajs/react';
import { useEffect } from 'react';

import { IconCheck } from '@/components/ui/icons';
import CountdownTimer from '@/components/thank-you/CountdownTimer';
import ProgressBar from '@/components/thank-you/ProgressBar';
import WhatsAppCTA from '@/components/thank-you/WhatsAppCTA';
import CaptureLayout from '@/layouts/CaptureLayout';
import type { ThankYouPageProps } from '@/types';

/**
 * ThankYou/Index — Post-capture urgency page.
 *
 * Drives leads to join the WhatsApp group with:
 * - Urgency headline ("NAO FECHE ESTA PAGINA!")
 * - Progress bar showing 2/3 steps completed
 * - WhatsApp CTA with pulse animation
 * - Countdown timer creating time pressure
 * - beforeunload prevention to reduce exits
 * - Footer with terms/privacy links
 */
export default function ThankYouIndex({ campaign, thank_you }: ThankYouPageProps) {
  const hasWhatsApp = !!thank_you.whatsapp_group_link;

  // Prevent accidental page close
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };

    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, []);

  return (
    <CaptureLayout>
      <Head title={`Obrigado - ${campaign.meta.title}`} />

      <div className="flex flex-col gap-6">
        {/* Urgency headline */}
        <div className="rounded-2xl bg-red-50 p-4 text-center shadow-md">
          <h1 className="text-xl font-extrabold tracking-tight text-red-600 sm:text-2xl">
            {thank_you.headline}
          </h1>
          <p className="mt-1 text-sm text-red-500">
            {thank_you.subheadline}
          </p>
        </div>

        {/* Main card */}
        <div className="rounded-2xl bg-[var(--color-surface)] p-6 shadow-2xl sm:p-8">
          {/* Success checkmark */}
          <div className="mb-5 flex justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-success)]/10">
              <IconCheck className="h-7 w-7 text-[var(--color-success)]" />
            </div>
          </div>

          {/* Progress bar */}
          <div className="mb-6">
            <ProgressBar
              targetPercentage={thank_you.progress_percentage}
              steps={thank_you.steps}
            />
          </div>

          {/* WhatsApp CTA */}
          {hasWhatsApp && (
            <div className="mb-6">
              <WhatsAppCTA
                groupLink={thank_you.whatsapp_group_link}
                buttonText={thank_you.whatsapp_button_text}
                showSocialProof={thank_you.show_social_proof}
                socialProofText={thank_you.social_proof_text}
              />
            </div>
          )}

          {/* Countdown */}
          <div className="border-t border-gray-100 pt-4">
            <CountdownTimer
              initialMinutes={thank_you.countdown_minutes}
              label="Tempo restante para garantir sua vaga"
            />
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-400">
          <Link
            href="/terms/"
            className="underline transition-colors hover:text-gray-600"
          >
            Termos de Uso
          </Link>
          {' | '}
          <Link
            href="/privacy/"
            className="underline transition-colors hover:text-gray-600"
          >
            Política de Privacidade
          </Link>
        </footer>
      </div>
    </CaptureLayout>
  );
}
