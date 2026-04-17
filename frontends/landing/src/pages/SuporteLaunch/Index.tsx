/**
 * SuporteLaunch (Launch Support) Page.
 *
 * Support page with a YouTube video background, Chatwoot integration,
 * and enrollment CTA. The Chatwoot widget auto-opens when loaded.
 *
 * All content is config-driven via Django Inertia props.
 *
 * Legacy: frontend-landing-pages/app/suporte-launch/page.tsx (90 lines)
 */
import { useEffect, useCallback } from 'react';
import { Head } from '@inertiajs/react';

import { VideoBackground } from '@/components/shared';
import WhatsAppFloatingButton from '@/components/WhatsAppFloatingButton';
import type { SuporteLaunchPageProps } from '@/types';

export default function SuporteLaunchPage({ config }: SuporteLaunchPageProps) {
  const { video_id, title, subtitle, cta_link, cta_text } = config;

  // Auto-open Chatwoot when it finishes loading
  const openChat = useCallback(() => {
    if (window.$chatwoot) {
      window.$chatwoot.toggle('open');
    }
  }, []);

  useEffect(() => {
    // Check if already loaded
    if (window.$chatwoot) {
      openChat();
      return;
    }

    // Listen for Chatwoot ready event
    const handler = () => openChat();
    window.addEventListener('chatwoot:ready', handler);
    return () => window.removeEventListener('chatwoot:ready', handler);
  }, [openChat]);

  return (
    <>
      <Head title={`${title} — Arthur Agrelli`} />

      {/* YouTube video background */}
      <VideoBackground videoId={video_id} overlayOpacity={0.52} zoom={1.2} />

      {/* Main content */}
      <main className="relative z-10 flex min-h-screen flex-col items-center justify-center p-4 pb-24 md:pb-4">
        <div className="mx-auto w-full max-w-4xl space-y-12">
          {/* Header */}
          <div className="animate-fade-in text-center">
            <h1 className="mb-4 text-4xl font-bold text-white md:text-5xl lg:text-6xl">
              {title}
            </h1>
            <p className="text-lg text-white/80 md:text-xl">{subtitle}</p>
          </div>

          {/* Loading indicator (shown before Chatwoot loads) */}
          <div className="flex justify-center" id="chatwoot-loading">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 text-center shadow-2xl backdrop-blur-md">
              <div className="flex items-center justify-center gap-3 text-white">
                <svg
                  className="h-6 w-6 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    className="opacity-25"
                  />
                  <path
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    fill="currentColor"
                    className="opacity-75"
                  />
                </svg>
                <span className="text-lg">Carregando atendimento...</span>
              </div>
            </div>
          </div>

          {/* Enrollment CTA */}
          <div className="mb-20 text-center md:mb-0">
            <a
              href={cta_link}
              className="inline-block transform rounded-xl bg-gradient-to-r from-[#0e036b] to-[#fb061a] px-8 py-4 text-lg font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-2xl md:text-xl"
            >
              {cta_text}
            </a>
          </div>
        </div>
      </main>

      {/* Floating button to (re)open Chatwoot */}
      <WhatsAppFloatingButton variant="default" mode="chatwoot" />
    </>
  );
}
