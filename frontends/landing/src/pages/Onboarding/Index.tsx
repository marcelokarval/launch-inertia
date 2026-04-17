/**
 * Onboarding (Post-Purchase) Page.
 *
 * Shown after successful checkout. Displays a marquee header confirming purchase,
 * instructional video, and WhatsApp floating button.
 *
 * All content is config-driven via Django Inertia props.
 *
 * Legacy: frontend-landing-pages/app/onboarding/page.tsx (158 lines)
 */
import { Head } from '@inertiajs/react';

import { MarqueeHeader, FullscreenBackground, YouTubeEmbed } from '@/components/shared';
import WhatsAppFloatingButton from '@/components/WhatsAppFloatingButton';
import type { OnboardingPageProps } from '@/types';

export default function OnboardingPage({ config }: OnboardingPageProps) {
  const {
    video_id,
    title,
    marquee_items,
    marquee_color,
    background_image,
    whatsapp_link,
  } = config;

  return (
    <>
      <Head title="Onboarding — Libere Seu Acesso" />

      {/* Full-viewport background */}
      <FullscreenBackground imageUrl={background_image} position="right center" />

      {/* Scrolling marquee header */}
      <MarqueeHeader items={marquee_items} bgColor={marquee_color} speed={30} />

      {/* Content */}
      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center px-4 pt-20 md:pt-24">
        {/* Title */}
        <h1 className="mb-6 mt-4 text-center text-3xl font-bold text-white md:mb-8 md:mt-6 md:text-4xl lg:text-5xl">
          {title}
        </h1>

        {/* Video */}
        <YouTubeEmbed videoId={video_id} title="Onboarding Video" autoplay />
      </div>

      {/* WhatsApp floating button */}
      {whatsapp_link ? (
        <WhatsAppFloatingButton variant="default" mode="whatsapp" href={whatsapp_link} />
      ) : (
        <WhatsAppFloatingButton variant="default" mode="chatwoot" />
      )}
    </>
  );
}
