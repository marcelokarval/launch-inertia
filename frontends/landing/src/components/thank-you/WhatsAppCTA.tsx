import { memo, useCallback, useEffect, useState } from 'react';

import { IconWhatsApp, IconLock } from '@/components/ui/icons';

interface WhatsAppCTAProps {
  /** WhatsApp group invite link */
  groupLink: string;
  /** Button text */
  buttonText?: string;
  /** Show social proof counter */
  showSocialProof?: boolean;
  /** Social proof text */
  socialProofText?: string;
  /** Auto-redirect countdown in seconds (0 or negative = disabled) */
  autoRedirectSeconds?: number;
}

/**
 * WhatsApp group CTA — green gradient pill, red GRATIS badge, auto-redirect.
 *
 * Matches legacy `components/thank-you-us/whatsapp-button.tsx`:
 * - Green gradient (from-green-600 to-green-500)
 * - Rounded-full pill shape
 * - Red "GRATIS" badge with wobble animation (-top-2 -right-2)
 * - Pulse ring behind the button
 * - Security text: lock icon + "100% Seguro e Gratuito"
 * - Social proof card (bg-gray-800/30)
 * - Auto-redirect countdown (configurable, default 30s)
 */
export default memo(function WhatsAppCTA({
  groupLink,
  buttonText = 'ENTRAR NO GRUPO VIP',
  showSocialProof = true,
  socialProofText = '247 pessoas entraram nos \u00faltimos 30 minutos',
  autoRedirectSeconds = 30,
}: WhatsAppCTAProps) {
  const [clicked, setClicked] = useState(false);
  const [timeLeft, setTimeLeft] = useState(autoRedirectSeconds);
  const isRedirectEnabled = autoRedirectSeconds > 0;

  const handleRedirect = useCallback(
    (method: 'auto' | 'click') => {
      // Track via CustomEvent
      window.dispatchEvent(
        new CustomEvent('whatsappGroupAction', {
          detail: { action: 'redirect', method, groupLink, timeLeft },
        }),
      );
      window.location.replace(groupLink);
    },
    [groupLink, timeLeft],
  );

  // Auto-redirect countdown
  useEffect(() => {
    if (!isRedirectEnabled) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          setTimeout(() => handleRedirect('auto'), 100);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isRedirectEnabled, handleRedirect]);

  return (
    <div className="w-full text-left">
      {/* Button container — relative for badge positioning */}
      <div className="relative inline-block w-full">
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            setClicked(true);
            handleRedirect('click');
          }}
          className={`relative flex w-full cursor-pointer items-center justify-center gap-2 rounded-full bg-gradient-to-r from-green-600 to-green-500 px-6 py-3 text-lg font-bold text-white shadow-xl transition-transform hover:scale-105 ${
            clicked ? 'opacity-75' : ''
          }`}
        >
          {/* Pulse ring */}
          <span className="absolute inset-0 animate-ping rounded-full bg-green-500 opacity-20" />

          {/* Content */}
          <span className="relative z-10 flex items-center gap-2">
            <IconWhatsApp className="h-6 w-6" />
            <span>{buttonText}</span>
          </span>
        </button>

        {/* GRATIS badge — wobble animation */}
        <span className="absolute -right-2 -top-2 z-10 animate-wobble rounded-full bg-red-500 px-2 py-1 text-xs font-bold text-white shadow">
          GR\u00c1TIS
        </span>

        {/* Auto-redirect timer */}
        {isRedirectEnabled && timeLeft > 0 && (
          <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-gray-400">
            {timeLeft}s
          </span>
        )}
      </div>

      {/* Security text */}
      <div className="mt-8 flex items-center gap-2 text-sm text-gray-400">
        <IconLock className="h-4 w-4" />
        <span>100% Seguro e Gratuito</span>
      </div>

      {/* Social proof */}
      {showSocialProof && (
        <div className="mt-3 hidden rounded-lg bg-gray-800/30 p-3 sm:inline-block">
          <p className="text-sm text-gray-300">
            <span className="font-semibold text-green-400">
              {socialProofText}
            </span>
          </p>
        </div>
      )}
    </div>
  );
});
