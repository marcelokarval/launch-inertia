import { useState } from 'react';

import { Head, Link } from '@inertiajs/react';

import ChatwootWidget from '@/components/support/ChatwootWidget';
import FAQPanel from '@/components/support/FAQPanel';
import { IconArrowLeft, IconHelpCircle, IconMessageCircle } from '@/components/ui/icons';
import type { SupportPageProps } from '@/types';

type MobileTab = 'chat' | 'faq';

/**
 * Support/Index — Central de Suporte page.
 *
 * Responsive layout:
 * - Mobile: pill tabs (Chat | FAQ), full-area per tab, only one visible at a time
 * - Desktop (lg+): side-by-side grid (FAQ left, Chat right), no tabs
 *
 * Components are always rendered (never unmounted) so Chatwoot keeps its
 * connection alive when switching to FAQ tab. Visibility is toggled via CSS.
 */
export default function SupportIndex({ support }: SupportPageProps) {
  const { chatwoot, faq_items, faq_categories } = support;
  const [activeTab, setActiveTab] = useState<MobileTab>('chat');

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

        {/* Mobile tab bar — hidden on desktop (lg:hidden) */}
        <div className="shrink-0 border-b border-zinc-800/50 px-4 py-3 lg:hidden">
          <div className="mx-auto flex max-w-md gap-2 rounded-xl bg-zinc-800/60 p-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                activeTab === 'chat'
                  ? 'bg-red-600 text-white shadow-lg shadow-red-900/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <IconMessageCircle className="h-4 w-4" />
              Chat
            </button>
            <button
              onClick={() => setActiveTab('faq')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                activeTab === 'faq'
                  ? 'bg-amber-600 text-white shadow-lg shadow-amber-900/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <IconHelpCircle className="h-4 w-4" />
              FAQ
            </button>
          </div>
        </div>

        {/* Content area */}
        <main className="flex-1 overflow-hidden p-4 md:p-6">
          <div className="mx-auto grid h-full max-w-7xl grid-cols-1 gap-4 overflow-hidden lg:grid-cols-2 lg:gap-6">
            {/*
              FAQ panel
              - Mobile: visible only when faq tab is active (hidden/flex toggle)
              - Desktop: always visible, order-1 (left column)
            */}
            <div
              className={`min-h-0 flex-col overflow-hidden lg:order-1 lg:flex ${
                activeTab === 'faq' ? 'flex' : 'hidden'
              }`}
            >
              {/* Section label — desktop only (mobile has tab bar) */}
              <div className="mb-3 hidden shrink-0 items-center gap-2 lg:flex">
                <IconHelpCircle className="h-5 w-5 text-amber-500" />
                <h2 className="font-semibold text-white">Perguntas Frequentes</h2>
              </div>
              <FAQPanel
                items={faq_items}
                categories={faq_categories}
                className="flex-1 overflow-hidden"
              />
            </div>

            {/*
              Chat panel
              - Mobile: visible only when chat tab is active (hidden/flex toggle)
              - Desktop: always visible, order-2 (right column)
            */}
            <div
              className={`min-h-0 flex-col overflow-hidden lg:order-2 lg:flex ${
                activeTab === 'chat' ? 'flex' : 'hidden'
              }`}
            >
              {/* Section label — desktop only (mobile has tab bar) */}
              <div className="mb-3 hidden shrink-0 items-center gap-2 lg:flex">
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
