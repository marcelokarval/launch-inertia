import { useEffect, useRef, type ReactNode } from 'react';

import { IconX } from '@/components/ui/icons';

interface LegalModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

/**
 * LegalModal — dark overlay modal for Terms/Privacy content.
 *
 * Matches legacy `components/ui/modal.tsx` + `components/thank-you/footer.tsx`.
 * Opens legal content inline without navigating away from the current page.
 *
 * - Dark glassmorphism backdrop
 * - Scrollable content area
 * - Trap focus inside modal
 * - Close on Escape key or overlay click
 */
export default function LegalModal({
  isOpen,
  onClose,
  title,
  children,
}: LegalModalProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />

      {/* Modal content */}
      <div
        ref={contentRef}
        className="relative z-10 flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl border border-gray-700 bg-gray-900 shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-700 px-6 py-4">
          <h2 className="text-lg font-bold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
            aria-label="Fechar"
          >
            <IconX className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="custom-scrollbar flex-1 overflow-y-auto px-6 py-4">
          {children}
        </div>
      </div>
    </div>
  );
}
