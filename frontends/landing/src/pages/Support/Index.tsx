import { Head, Link } from '@inertiajs/react';

import ChatwootWidget from '@/components/support/ChatwootWidget';
import FAQPanel from '@/components/support/FAQPanel';
import type { SupportPageProps } from '@/types';

/**
 * Support/Index — Central de Suporte page.
 *
 * Two-panel layout:
 * - Desktop: FAQ left, Chat right (grid 2-col)
 * - Mobile: Chat on top (60vh), FAQ below (50vh)
 *
 * Dark theme to match the Chatwoot widget aesthetic.
 * All config comes from Django props (Chatwoot token, FAQ items, etc.).
 */
export default function SupportIndex({ support }: SupportPageProps) {
  const { chatwoot, faq_items, faq_categories } = support;

  return (
    <div className="h-screen overflow-hidden bg-black">
      <Head title="Central de Suporte" />

      {/* Background gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-zinc-900 via-black to-zinc-900" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-red-900/10 via-transparent to-transparent" />

      {/* Content */}
      <div className="relative z-10 flex h-full flex-col overflow-hidden">
        {/* Header */}
        <header className="shrink-0 border-b border-zinc-800/50 p-4 md:p-6">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-2 text-gray-400 transition-colors hover:text-white"
            >
              {/* ArrowLeft icon */}
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              <span className="text-sm">Voltar</span>
            </Link>

            <h1 className="text-xl font-bold md:text-2xl">
              <span className="bg-gradient-to-r from-red-500 to-amber-500 bg-clip-text text-transparent">
                Central de Suporte
              </span>
            </h1>

            {/* Spacer for centering */}
            <div className="w-20" />
          </div>
        </header>

        {/* Main panels */}
        <main className="flex-1 overflow-hidden p-4 md:p-6">
          <div className="mx-auto h-full max-w-7xl overflow-hidden">
            {/* Mobile layout: chat top, FAQ below */}
            <div className="flex h-full flex-col gap-4 lg:hidden">
              {/* Chat — mobile */}
              <div className="h-[60vh] min-h-[400px]">
                <div className="mb-3 flex items-center gap-2">
                  <svg className="h-5 w-5 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                  </svg>
                  <h2 className="font-semibold text-white">Chat ao Vivo</h2>
                </div>
                <ChatwootWidget config={chatwoot} className="h-[calc(100%-32px)]" />
              </div>

              {/* FAQ — mobile */}
              <div className="h-[50vh] min-h-[350px]">
                <div className="mb-3 flex items-center gap-2">
                  <svg className="h-5 w-5 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <h2 className="font-semibold text-white">Perguntas Frequentes</h2>
                </div>
                <FAQPanel
                  items={faq_items}
                  categories={faq_categories}
                  className="h-[calc(100%-32px)]"
                />
              </div>
            </div>

            {/* Desktop layout: FAQ left, Chat right */}
            <div className="hidden h-full gap-6 overflow-hidden lg:grid lg:grid-cols-2">
              {/* FAQ — desktop (left) */}
              <div className="flex flex-col overflow-hidden">
                <div className="mb-3 flex shrink-0 items-center gap-2">
                  <svg className="h-5 w-5 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <h2 className="font-semibold text-white">Perguntas Frequentes</h2>
                </div>
                <FAQPanel
                  items={faq_items}
                  categories={faq_categories}
                  className="flex-1 overflow-hidden"
                />
              </div>

              {/* Chat — desktop (right) */}
              <div className="flex flex-col overflow-hidden">
                <div className="mb-3 flex shrink-0 items-center gap-2">
                  <svg className="h-5 w-5 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                  </svg>
                  <h2 className="font-semibold text-white">Chat ao Vivo</h2>
                </div>
                <ChatwootWidget config={chatwoot} className="flex-1 overflow-hidden" />
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="shrink-0 border-t border-zinc-800/50 p-4">
          <div className="mx-auto max-w-7xl text-center">
            <p className="text-xs text-gray-500">{chatwoot.business_hours}</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
