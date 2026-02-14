import { type ReactNode } from 'react';

interface LandingLayoutProps {
  children: ReactNode;
}

/**
 * Base layout for all landing pages.
 * No sidebar, no auth, minimal chrome.
 * Each campaign may wrap content in campaign-specific sub-layouts.
 */
export default function LandingLayout({ children }: LandingLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1">
        {children}
      </main>
      <footer className="py-6 text-center text-sm text-[var(--color-text-muted)]">
        <p>&copy; {new Date().getFullYear()} Arthur Agrelli. Todos os direitos reservados.</p>
      </footer>
    </div>
  );
}
