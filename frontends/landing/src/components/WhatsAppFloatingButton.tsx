import { memo, useEffect, useState } from 'react';

import { IconWhatsApp } from '@/components/ui/icons';

type ButtonVariant = 'default' | 'amber' | 'green';
type ButtonMode = 'whatsapp' | 'chatwoot';

interface WhatsAppFloatingButtonProps {
  /** WhatsApp link (wa.me/...) — used when mode is 'whatsapp' */
  href?: string;
  /** Mode: 'whatsapp' opens link, 'chatwoot' toggles live chat */
  mode?: ButtonMode;
  /** Color variant */
  variant?: ButtonVariant;
  /** Tooltip text shown after delay */
  tooltip?: string;
  /** Delay before showing the button (ms). Default: 3000 */
  showDelay?: number;
  /** Delay before showing tooltip (ms). Default: 10000 */
  tooltipDelay?: number;
}

const variantClasses: Record<ButtonVariant, string> = {
  default: 'bg-[#E50914] hover:bg-[#c5080f]',
  amber: 'bg-amber-500 hover:bg-amber-600',
  green: 'bg-green-500 hover:bg-green-600',
};

const pingClasses: Record<ButtonVariant, string> = {
  default: 'bg-[#E50914]',
  amber: 'bg-amber-500',
  green: 'bg-green-500',
};

/**
 * WhatsAppFloatingButton — fixed bottom-right button.
 *
 * Matches legacy `components/whatsapp-button.tsx`:
 * - Fixed position, bottom-6 right-6, z-50
 * - 3 color variants (default/red, amber, green)
 * - 2 modes: whatsapp (opens wa.me) or chatwoot (toggles chat)
 * - Entrance delay (default 3s)
 * - Tooltip after 10s
 * - Ping animation
 */
export default memo(function WhatsAppFloatingButton({
  href = '#',
  mode = 'whatsapp',
  variant = 'default',
  tooltip = 'Precisa de ajuda?',
  showDelay = 3000,
  tooltipDelay = 10000,
}: WhatsAppFloatingButtonProps) {
  const [visible, setVisible] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipDismissed, setTooltipDismissed] = useState(false);

  // Entrance delay
  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), showDelay);
    return () => clearTimeout(timer);
  }, [showDelay]);

  // Tooltip delay
  useEffect(() => {
    if (!visible || tooltipDismissed) return;
    const timer = setTimeout(() => setShowTooltip(true), tooltipDelay - showDelay);
    return () => clearTimeout(timer);
  }, [visible, tooltipDelay, showDelay, tooltipDismissed]);

  const handleClick = () => {
    setShowTooltip(false);
    setTooltipDismissed(true);

    if (mode === 'chatwoot' && window.$chatwoot) {
      window.$chatwoot.toggle('open');
    } else if (mode === 'whatsapp') {
      window.open(href, '_blank', 'noopener,noreferrer');
    }
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3">
      {/* Tooltip */}
      {showTooltip && !tooltipDismissed && (
        <div className="animate-fade-in rounded-lg bg-gray-800 px-3 py-2 text-sm text-white shadow-lg">
          <span>{tooltip}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowTooltip(false);
              setTooltipDismissed(true);
            }}
            className="ml-2 cursor-pointer text-gray-400 hover:text-white"
            aria-label="Fechar tooltip"
          >
            &times;
          </button>
        </div>
      )}

      {/* Button */}
      <button
        onClick={handleClick}
        className={`relative flex h-14 w-14 cursor-pointer items-center justify-center rounded-full shadow-lg transition-transform hover:scale-110 ${variantClasses[variant]}`}
        aria-label="Abrir WhatsApp"
      >
        {/* Ping animation */}
        <span
          className={`absolute inset-0 animate-ping rounded-full opacity-30 ${pingClasses[variant]}`}
        />
        <IconWhatsApp className="relative z-10 h-7 w-7 text-white" />
      </button>
    </div>
  );
});
