import { type ReactNode } from 'react';

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

      {/* Content — left-aligned like legacy */}
      <div className="relative z-10 flex min-h-screen w-full flex-col justify-start px-5 pt-[7vh] md:px-6 lg:px-8">
        <div className="w-full max-w-[var(--max-width-form)] animate-fade-in pb-10 sm:ml-[10%] md:ml-[50px]">
          {children}
        </div>
      </div>
    </div>
  );
}
