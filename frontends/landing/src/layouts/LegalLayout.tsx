import { Link } from '@inertiajs/react';
import { type ReactNode } from 'react';

import { IconArrowLeft } from '@/components/ui/icons';

interface LegalLayoutProps {
  children: ReactNode;
  title: string;
  version?: string;
  lastUpdated?: string;
}

/**
 * Layout for legal pages (terms, privacy).
 *
 * Clean, readable layout with proper typography for legal text.
 * Light background, constrained width for comfortable reading.
 */
export default function LegalLayout({
  children,
  title,
  version,
  lastUpdated,
}: LegalLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-3xl px-4 py-6">
          <Link
            href="/"
            className="mb-2 inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800"
          >
            <IconArrowLeft className="h-4 w-4" /> Voltar ao início
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {(version || lastUpdated) && (
            <p className="mt-1 text-sm text-gray-500">
              {version && <span>{version}</span>}
              {version && lastUpdated && <span> &middot; </span>}
              {lastUpdated && <span>Última atualização: {lastUpdated}</span>}
            </p>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">
        <div className="rounded-lg bg-white p-6 shadow-sm sm:p-8">
          {children}
        </div>
      </main>
      <footer className="border-t border-gray-200 bg-white">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <p className="text-center text-xs text-gray-400">
            &copy; {new Date().getFullYear()} Arthur Agrelli. Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
