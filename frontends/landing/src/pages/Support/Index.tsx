import { Head, Link } from '@inertiajs/react';

import ChatwootWidget from '@/components/support/ChatwootWidget';
import FAQPanel from '@/components/support/FAQPanel';
import { IconArrowLeft, IconHelpCircle, IconMessageCircle } from '@/components/ui/icons';
import type { SupportPageProps } from '@/types';

/**
 * Support/Index — Central de Suporte page.
 *
 * Single responsive layout — components rendered once, CSS handles reflow.
 * - Desktop: FAQ left, Chat right (grid 2-col)
 * - Mobile: stacked (chat first via order, then FAQ)
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
              <IconArrowLeft className="h-4 w-4" />
              <span className="text-sm">Voltar</span>
            </Link>

            <h1 className="text-xl font-bold md:text-2xl">
              <span className="bg-gradient-to-r from-red-500 to-amber-500 bg-clip-text text-transparent">
                Central de Suporte
              </span>
            </h1>

            <div className="w-20" />
          </div>
        </header>

        {/* Single responsive grid — components rendered once */}
        <main className="flex-1 overflow-hidden p-4 md:p-6">
          <div className="mx-auto grid h-full max-w-7xl grid-cols-1 gap-4 overflow-hidden lg:grid-cols-2 lg:gap-6">
            {/* FAQ panel — order-2 on mobile (below chat), order-1 on desktop (left) */}
            <div className="flex min-h-[300px] flex-col overflow-hidden order-2 lg:order-1">
              <div className="mb-3 flex shrink-0 items-center gap-2">
                <IconHelpCircle className="h-5 w-5 text-amber-500" />
                <h2 className="font-semibold text-white">Perguntas Frequentes</h2>
              </div>
              <FAQPanel
                items={faq_items}
                categories={faq_categories}
                className="flex-1 overflow-hidden"
              />
            </div>

            {/* Chat panel — order-1 on mobile (above FAQ), order-2 on desktop (right) */}
            <div className="flex min-h-[350px] flex-col overflow-hidden order-1 lg:order-2">
              <div className="mb-3 flex shrink-0 items-center gap-2">
                <IconMessageCircle className="h-5 w-5 text-red-500" />
                <h2 className="font-semibold text-white">Chat ao Vivo</h2>
              </div>
              <ChatwootWidget config={chatwoot} className="flex-1 overflow-hidden" />
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
