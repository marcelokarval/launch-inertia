/**
 * Hero section for the RecadoImportante sales page.
 *
 * Full-viewport background image with centered YouTube video embed
 * and a prominent WhatsApp CTA button below.
 */
import { YouTubeEmbed } from '@/components/shared';

interface HeroVideoProps {
  /** YouTube video ID */
  videoId: string;
  /** Background image URL */
  bgImage?: string;
  /** WhatsApp CTA link */
  ctaLink: string;
  /** CTA button text */
  ctaText: string;
  /** Opening date text (e.g., "26 de Janeiro às 19h30") */
  openingDate?: string;
  /** Disclaimer text */
  disclaimer?: string;
}

export default function HeroVideo({
  videoId,
  bgImage,
  ctaLink,
  ctaText,
  openingDate,
  disclaimer,
}: HeroVideoProps) {
  return (
    <section className="relative min-h-screen bg-white pt-16 md:pt-20">
      {/* Background image */}
      {bgImage && (
        <div className="absolute inset-0 z-0">
          <img
            src={bgImage}
            alt=""
            className="h-full w-full object-cover"
            loading="eager"
            aria-hidden="true"
          />
          <div className="absolute inset-0 bg-black/40" />
        </div>
      )}

      <div className="relative z-10 mx-auto flex max-w-4xl flex-col items-center px-4 py-12 md:py-16">
        {/* Opening date badge */}
        {openingDate && (
          <div className="mb-6 rounded-full bg-red-600 px-6 py-2 text-sm font-bold text-white md:text-base">
            {openingDate}
          </div>
        )}

        {/* Video */}
        <div className="w-full">
          <YouTubeEmbed videoId={videoId} title="Apresentação" autoplay />
        </div>

        {/* CTA */}
        <a
          href={ctaLink}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-8 w-full max-w-md transform rounded-xl bg-green-500 px-8 py-4 text-center text-lg font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:bg-green-600 hover:shadow-xl md:text-xl"
        >
          {ctaText}
        </a>

        {disclaimer && (
          <p className="mt-3 text-center text-xs text-white/60 md:text-sm">
            {disclaimer}
          </p>
        )}
      </div>
    </section>
  );
}
