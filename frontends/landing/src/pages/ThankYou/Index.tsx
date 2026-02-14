import { Head } from '@inertiajs/react';
import { useEffect } from 'react';

import LandingFooter from '@/components/LandingFooter';
import CountdownTimer from '@/components/thank-you/CountdownTimer';
import ProgressBar from '@/components/thank-you/ProgressBar';
import RedBanner from '@/components/thank-you/RedBanner';
import WhatsAppCTA from '@/components/thank-you/WhatsAppCTA';
import type { ThankYouPageProps } from '@/types';

/**
 * ThankYou/Index — Post-capture urgency page.
 *
 * Matches legacy `app/(thankyou)/obrigado-us/page.tsx`:
 * - RedBanner at top (full-width, pulsing text)
 * - Black background
 * - Centered max-w-2xl content
 * - SimpleHeadline (NÃO FECHE... GRUPO VIP)
 * - Red progress bar at 90% with stripes
 * - Instruction paragraph in white
 * - WhatsApp CTA button (green gradient, GRÁTIS badge, auto-redirect)
 * - CountdownTimer
 * - Dark footer with terms/privacy links
 * - beforeunload prevention
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
    <>
      <Head title={`Obrigado - ${campaign.meta.title}`} />

      {/* Red banner at the very top */}
      <RedBanner />

      {/* Main content — black bg */}
      <div className="relative flex min-h-screen flex-col bg-black">
        <div className="relative z-10 flex flex-grow flex-col justify-center px-4 py-12">
          <div className="mx-auto w-full max-w-2xl space-y-8">
            {/* Urgency headline */}
            <div className="space-y-2 text-center md:space-y-4">
              <h1 className="text-xl font-bold leading-tight text-white sm:text-2xl md:text-4xl lg:text-5xl">
                <span className="text-red-500">NÃO FECHE</span> ESTA PÁGINA
                ANTES DE
                <br className="hidden sm:block" />
                <span className="sm:hidden"> </span>ENTRAR NO{' '}
                <span className="text-green-400 underline">GRUPO VIP</span> DA
                <br className="hidden sm:block" />
                <span className="sm:hidden"> </span>MENTORIA GRATUITA
              </h1>
              <p className="animate-pulse text-sm font-semibold text-yellow-400 sm:text-lg md:text-xl lg:text-2xl">
                ESTA PÁGINA NÃO APARECERÁ NOVAMENTE
              </p>
            </div>

            {/* Progress bar — red, 90%, with stripes */}
            <ProgressBar
              targetPercentage={thank_you.progress_percentage || 90}
              steps={thank_you.steps}
            />

            {/* Instruction text */}
            <p className="text-left text-lg text-white md:text-xl">
              Para receber avisos, materiais e garantir que você não perca nada
              do nosso evento, clique no botão abaixo e entre para o grupo VIP
              no WhatsApp:
            </p>

            {/* WhatsApp CTA */}
            {hasWhatsApp && (
              <WhatsAppCTA
                groupLink={thank_you.whatsapp_group_link}
                buttonText={thank_you.whatsapp_button_text}
                showSocialProof={thank_you.show_social_proof}
                socialProofText={thank_you.social_proof_text}
                autoRedirectSeconds={30}
              />
            )}

            {/* Countdown timer */}
            <CountdownTimer
              initialMinutes={thank_you.countdown_minutes}
              label="Tempo restante para garantir sua vaga"
            />
          </div>
        </div>

        {/* Footer — dark with legal modals */}
        <LandingFooter />
      </div>
    </>
  );
}
