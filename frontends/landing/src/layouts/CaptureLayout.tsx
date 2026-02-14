import { type ReactNode } from 'react';

interface CaptureLayoutProps {
  children: ReactNode;
}

/**
 * Layout for capture/lead-gen pages.
 *
 * Centered single-column, no navigation, optimized for conversions.
 * Different from LandingLayout (which has a footer).
 */
export default function CaptureLayout({ children }: CaptureLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface-dark)]">
      <main className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-[var(--max-width-form)] animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
