import LegalLayout from '@/layouts/LegalLayout';
import PrivacyContent from '@/components/legal/PrivacyContent';

/**
 * Privacy Policy page.
 *
 * Static legal content — US jurisdiction, CCPA compliant.
 * Content extracted to PrivacyContent for reuse in LegalModal.
 */
export default function Privacy() {
  return (
    <LegalLayout
      title="Privacy Policy"
      version="Version 2.0 — US Privacy Policy"
      lastUpdated="February 2026"
    >
      <PrivacyContent />
    </LegalLayout>
  );
}
