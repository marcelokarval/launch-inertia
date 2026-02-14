import LegalLayout from '@/layouts/LegalLayout';
import TermsContent from '@/components/legal/TermsContent';

/**
 * Terms of Service page.
 *
 * Static legal content — US jurisdiction, CCPA/FTC compliant.
 * Content extracted to TermsContent for reuse in LegalModal.
 */
export default function Terms() {
  return (
    <LegalLayout
      title="Terms of Service"
      version="Version 2.0 — US Subscription Service Terms"
      lastUpdated="February 2026"
    >
      <TermsContent />
    </LegalLayout>
  );
}
