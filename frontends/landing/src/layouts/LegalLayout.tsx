import { Link } from '@inertiajs/react';
import { type ReactNode } from 'react';

interface LegalLayoutProps {
  children: ReactNode;
  title: string;
  version?: string;
  lastUpdated?: string;
}

/**
 * Layout for legal pages (terms, privacy).
 *
 * Dark glassmorphism theme matching legacy Next.js design:
 * - Gradient background (gray-900 via gray-800 to black)
 * - Semi-transparent card with backdrop-blur
 * - Green "Back to Home" pill button
 */
export default function LegalLayout({
  children,
  title,
  version,
  lastUpdated,
}: LegalLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black">
      <div className="container mx-auto max-w-4xl px-4 py-12">
        {/* Title */}
        <h1 className="mb-8 text-center text-3xl font-bold text-white md:text-4xl">
          {title}
        </h1>

        {/* Content card */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-6 backdrop-blur-sm md:p-8">
          {children}

          {/* Footer inside card */}
          <div className="mt-8 border-t border-gray-700 pt-6">
            <div className="flex flex-col items-center gap-4">
              {(version || lastUpdated) && (
                <p className="text-sm text-gray-400">
                  {version && <span>{version}</span>}
                  {version && lastUpdated && <span> &middot; </span>}
                  {lastUpdated && <span>Última atualização: {lastUpdated}</span>}
                </p>
              )}

              <Link
                href="/"
                className="inline-block rounded-full bg-green-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-green-700"
              >
                Voltar ao início
              </Link>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <p className="mt-8 text-center text-xs text-gray-500">
          &copy; {new Date().getFullYear()} Arthur Agrelli. Todos os direitos reservados.
        </p>
      </div>
    </div>
  );
}
