import { type ReactNode } from 'react';

import LandingFooter from '@/components/LandingFooter';

interface CaptureLayoutProps {
  children: ReactNode;
  /** Optional full-screen background image URL (from campaign JSON). */
  backgroundImage?: string;
}

/**
 * Layout for capture/lead-gen pages.
 *
 * Dark theme, left-aligned content (max-w-570px), no navigation.
 * Matches legacy inscrever-wh-rc-v3-layout.tsx visual identity.
 *
 * Supports optional background image with dark overlay.
 * Footer with legal modals at bottom (matches legacy capture pages).
 */
export default function CaptureLayout({
  children,
  backgroundImage,
}: CaptureLayoutProps) {
  return (
    <div className="relative min-h-screen bg-[var(--color-surface-dark)]">
      {/* Background image (optional) with dark overlay */}
      {backgroundImage && (
        <>
          <div
            className="fixed inset-0 bg-cover bg-center bg-no-repeat"
            style={{ backgroundImage: `url(${backgroundImage})` }}
          />
          <div className="fixed inset-0 bg-black/60" />
        </>
      )}

      {/* Content + footer — flex column to push footer down */}
      <div className="relative z-10 flex min-h-screen w-full flex-col">
        <div className="flex-grow px-5 pt-[7vh] md:px-6 lg:px-8">
          <div className="w-full max-w-[var(--max-width-form)] animate-fade-in pb-10 sm:ml-[10%] md:ml-[50px]">
            {children}
          </div>
        </div>

        {/* Footer — dark with legal modals */}
        <LandingFooter />
      </div>
    </div>
  );
}
