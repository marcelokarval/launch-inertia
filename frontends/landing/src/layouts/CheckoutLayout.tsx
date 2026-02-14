import { type ReactNode } from 'react';

import WhatsAppFloatingButton from '@/components/WhatsAppFloatingButton';

interface CheckoutLayoutProps {
  children: ReactNode;
  title?: string;
}

/**
 * Layout for checkout/payment pages.
 *
 * Dark theme, minimal layout focused on payment flow.
 * No distracting navigation — just title + content.
 * WhatsApp floating button (green, chatwoot mode) matches legacy checkout pages.
 */
export default function CheckoutLayout({ children, title }: CheckoutLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface-dark)]">
      {title && (
        <header className="border-b border-gray-800 px-4 py-4">
          <h1 className="text-center text-lg font-semibold text-white">
            {title}
          </h1>
        </header>
      )}
      <main className="flex flex-1 items-start justify-center px-4 py-8">
        <div className="w-full max-w-2xl">
          {children}
        </div>
      </main>

      {/* WhatsApp floating button — green variant, chatwoot mode (legacy parity) */}
      <WhatsAppFloatingButton variant="green" mode="chatwoot" />
    </div>
  );
}
