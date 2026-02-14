import { useState } from 'react';

import LegalModal from '@/components/legal/LegalModal';
import TermsContent from '@/components/legal/TermsContent';
import PrivacyContent from '@/components/legal/PrivacyContent';

interface LandingFooterProps {
  /** Copyright owner name */
  copyrightName?: string;
}

/**
 * LandingFooter — dark footer with legal modals and Facebook disclaimer.
 *
 * Matches legacy `components/thank-you/footer.tsx`:
 * - bg-black/50 backdrop-blur-sm border-t border-gray-800
 * - Terms/Privacy open in modals (not page navigation)
 * - Copyright line
 * - Facebook disclaimer
 *
 * Used in ThankYou, Capture, and any page that needs the full footer.
 */
export default function LandingFooter({
  copyrightName = 'Mestre das Casas Baratas no EUA',
}: LandingFooterProps) {
  const [isTermsOpen, setIsTermsOpen] = useState(false);
  const [isPrivacyOpen, setIsPrivacyOpen] = useState(false);

  return (
    <>
      <footer className="mt-auto border-t border-gray-800 bg-black/50 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl px-4 py-6">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            {/* Legal links — open modals */}
            <div className="flex items-center gap-6 text-sm">
              <button
                onClick={() => setIsTermsOpen(true)}
                className="cursor-pointer text-gray-400 transition-colors hover:text-white"
              >
                Termos de Uso
              </button>
              <span className="text-gray-600">&bull;</span>
              <button
                onClick={() => setIsPrivacyOpen(true)}
                className="cursor-pointer text-gray-400 transition-colors hover:text-white"
              >
                Política de Privacidade
              </button>
            </div>

            {/* Copyright */}
            <div className="text-center text-sm text-gray-400 md:text-right">
              <p>
                Todos os direitos reservados &mdash;{' '}
                <span className="font-semibold text-white">{copyrightName}</span>
              </p>
            </div>
          </div>

          {/* Facebook disclaimer */}
          <div className="mt-4 border-t border-gray-800 pt-4">
            <p className="text-center text-xs text-gray-500">
              Este site não é afiliado ao Facebook ou a qualquer entidade do
              Facebook. Após sair do Facebook, a responsabilidade é nossa, não
              deles. Fazemos todos os esforços para indicar claramente e mostrar
              todas as evidências dos produtos e usar resultados reais.
            </p>
          </div>
        </div>
      </footer>

      {/* Legal modals */}
      <LegalModal
        isOpen={isTermsOpen}
        onClose={() => setIsTermsOpen(false)}
        title="Terms of Service"
      >
        <TermsContent />
      </LegalModal>

      <LegalModal
        isOpen={isPrivacyOpen}
        onClose={() => setIsPrivacyOpen(false)}
        title="Privacy Policy"
      >
        <PrivacyContent />
      </LegalModal>
    </>
  );
}
