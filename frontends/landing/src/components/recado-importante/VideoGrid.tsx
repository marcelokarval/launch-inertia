/**
 * 2x2 grid of YouTube testimonial videos.
 *
 * Lazy-loaded thumbnails that load the iframe on click.
 * Uses the shared YouTubeEmbed component.
 */
import { useState } from 'react';

import type { VideoTestimonial } from '@/types';

interface VideoGridProps {
  testimonials: VideoTestimonial[];
  /** Background image URL for the section */
  bgImage?: string;
}

function VideoCard({ testimonial }: { testimonial: VideoTestimonial }) {
  const [playing, setPlaying] = useState(false);
  const thumbUrl = `https://img.youtube.com/vi/${testimonial.video_id}/hqdefault.jpg`;

  return (
    <div className="overflow-hidden rounded-xl">
      {!playing ? (
        <button
          onClick={() => setPlaying(true)}
          className="group relative aspect-video w-full"
          aria-label={`Assistir depoimento de ${testimonial.name}`}
        >
          <img
            src={thumbUrl}
            alt={testimonial.name}
            className="h-full w-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 transition-colors group-hover:bg-black/50">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-600 shadow-lg transition-transform group-hover:scale-110">
              <svg
                viewBox="0 0 24 24"
                fill="white"
                className="ml-1 h-6 w-6"
                aria-hidden="true"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
            <p className="text-sm font-bold text-white">{testimonial.name}</p>
            {testimonial.description && (
              <p className="text-xs text-white/70">{testimonial.description}</p>
            )}
          </div>
        </button>
      ) : (
        <div className="aspect-video">
          <iframe
            src={`https://www.youtube.com/embed/${testimonial.video_id}?autoplay=1&rel=0&modestbranding=1`}
            className="h-full w-full border-0"
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
            title={`Depoimento de ${testimonial.name}`}
          />
        </div>
      )}
    </div>
  );
}

export default function VideoGrid({ testimonials, bgImage }: VideoGridProps) {
  if (!testimonials.length) return null;

  return (
    <section className="relative px-4 py-12 md:py-16">
      {bgImage && (
        <div className="absolute inset-0 z-0">
          <img
            src={bgImage}
            alt=""
            className="h-full w-full object-cover"
            loading="lazy"
            aria-hidden="true"
          />
          <div className="absolute inset-0 bg-black/60" />
        </div>
      )}

      <div className="relative z-10 mx-auto max-w-5xl">
        <h2 className="mb-8 text-center text-2xl font-bold text-white md:text-3xl">
          O que nossos alunos dizem
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6">
          {testimonials.map((t) => (
            <VideoCard key={t.video_id} testimonial={t} />
          ))}
        </div>
      </div>
    </section>
  );
}
