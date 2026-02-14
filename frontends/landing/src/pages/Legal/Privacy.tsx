import Section from '@/components/legal/Section';
import LegalLayout from '@/layouts/LegalLayout';

/**
 * Privacy Policy page.
 *
 * Static legal content — US jurisdiction, CCPA compliant.
 * Ported from legacy Next.js frontend-landing-pages.
 */
export default function Privacy() {
  return (
    <LegalLayout
      title="Privacy Policy"
      version="Version 2.0 — US Privacy Policy"
      lastUpdated="February 2026"
    >
      <div className="space-y-6 text-sm leading-relaxed text-gray-300">
        <Section title="1. Data Controller & Legal Basis">
          <p className="mb-2">
            We are a United States company that collects and processes personal data.
            This Privacy Policy complies with applicable US privacy laws including:
          </p>
          <ul className="list-disc space-y-1 pl-6">
            <li>California Consumer Privacy Act (CCPA) for California residents</li>
            <li>Nevada Privacy Law (NRS 603A) for Nevada residents</li>
            <li>Federal Trade Commission (FTC) regulations</li>
            <li>State privacy laws of Virginia, Colorado, Connecticut where applicable</li>
          </ul>
        </Section>

        <Section title="2. Information We Collect">
          <p className="mb-2"><strong>Personal Information:</strong></p>
          <ul className="mb-3 list-disc space-y-1 pl-6">
            <li>Name and contact details (email, phone/WhatsApp number)</li>
            <li>Payment information (processed securely via Stripe)</li>
            <li>Account credentials and preferences</li>
            <li>Communication history and support requests</li>
          </ul>
          <p className="mb-2"><strong>Automatically Collected Data:</strong></p>
          <ul className="list-disc space-y-1 pl-6">
            <li>IP address and approximate location (country, state, city)</li>
            <li>Device information (type, browser, operating system)</li>
            <li>Usage data (pages visited, time spent, clicks)</li>
            <li>Cookies and similar tracking technologies</li>
          </ul>
        </Section>

        <Section title="3. How We Use Your Information">
          <p className="mb-2">We use your information to:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li>Provide and manage your subscription services</li>
            <li>Process payments and prevent fraud</li>
            <li>Send service-related communications</li>
            <li>Send marketing messages (with your consent)</li>
            <li>Improve our services and user experience</li>
            <li>Comply with legal obligations</li>
            <li>Analyze usage patterns and optimize content</li>
          </ul>
        </Section>

        <Section title="4. Marketing Communications & Consent">
          <p className="mb-2"><strong>With your explicit consent, we may:</strong></p>
          <ul className="mb-3 list-disc space-y-1 pl-6">
            <li>Send promotional emails about our educational content</li>
            <li>Contact you via WhatsApp Business API with updates and offers</li>
            <li>Create custom audiences for targeted advertising on Meta platforms</li>
            <li>Send SMS messages about important updates (if opted in)</li>
          </ul>
          <p>
            <strong>Opt-Out:</strong> You can unsubscribe from marketing communications at any time
            by clicking the unsubscribe link in emails, replying &ldquo;STOP&rdquo; to messages, or
            contacting us directly. This does not affect service-related communications.
          </p>
        </Section>

        <Section title="5. Data Sharing & Third-Party Services">
          <p className="mb-2">We share your data only with:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li><strong>Stripe:</strong> For secure payment processing (PCI-DSS compliant)</li>
            <li><strong>Meta Platforms:</strong> For advertising and remarketing (Facebook/Instagram)</li>
            <li><strong>Google:</strong> For analytics and advertising services</li>
            <li><strong>WhatsApp:</strong> For business communications via official API</li>
            <li><strong>Service providers:</strong> Who assist in operating our services under strict agreements</li>
          </ul>
          <p className="mt-2">We DO NOT sell your personal information to third parties.</p>
        </Section>

        <Section title="6. Cookies & Tracking Technologies">
          <p className="mb-2">We use the following technologies:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li><strong>Essential Cookies:</strong> Required for site functionality (no consent needed)</li>
            <li><strong>Analytics Cookies:</strong> Google Analytics 4 with IP anonymization</li>
            <li><strong>Marketing Cookies:</strong> Meta Pixel for conversion tracking (requires consent)</li>
            <li><strong>FingerprintJS:</strong> For fraud prevention and security</li>
          </ul>
          <p className="mt-2">
            You can manage cookie preferences through your browser settings. Disabling cookies
            may limit site functionality.
          </p>
        </Section>

        <Section title="7. Your Privacy Rights">
          <p className="mb-2"><strong>All Users Have the Right to:</strong></p>
          <ul className="mb-3 list-disc space-y-1 pl-6">
            <li>Access your personal information</li>
            <li>Correct inaccurate data</li>
            <li>Delete your account and data (subject to legal requirements)</li>
            <li>Opt-out of marketing communications</li>
            <li>Data portability (receive your data in a structured format)</li>
          </ul>
          <p className="mb-2"><strong>California Residents (CCPA Rights):</strong></p>
          <ul className="list-disc space-y-1 pl-6">
            <li>Right to know what personal information we collect</li>
            <li>Right to know if we sell or share personal information (we don&apos;t)</li>
            <li>Right to opt-out of sale (not applicable as we don&apos;t sell data)</li>
            <li>Right to non-discrimination for exercising privacy rights</li>
          </ul>
          <p className="mt-2">
            To exercise your rights, contact us at the email provided. We respond within 30 days.
          </p>
        </Section>

        <Section title="8. Data Security">
          <p>
            We implement appropriate technical and organizational measures including:
            SSL/TLS encryption for data in transit, secure servers for data at rest,
            access controls, regular security audits, and employee training. However,
            no method of transmission over the internet is 100% secure.
          </p>
        </Section>

        <Section title="9. Data Retention">
          <p className="mb-2">We retain your data for:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li>Active accounts: Duration of subscription plus 5 years for tax purposes</li>
            <li>Marketing data: Until consent is withdrawn</li>
            <li>Analytics data: 2 years or per Google Analytics settings</li>
            <li>Payment records: As required by financial regulations</li>
          </ul>
          <p className="mt-2">After retention periods, data is permanently deleted or anonymized.</p>
        </Section>

        <Section title="10. Platform Compliance">
          <p className="mb-2"><strong>Meta/Facebook Compliance:</strong></p>
          <ul className="mb-3 list-disc space-y-1 pl-6">
            <li>We comply with Meta&apos;s Data Use Restrictions</li>
            <li>Custom Audiences created following Meta policies</li>
            <li>Clear opt-out mechanisms provided</li>
          </ul>
          <p className="mb-2"><strong>WhatsApp Business Compliance:</strong></p>
          <ul className="mb-3 list-disc space-y-1 pl-6">
            <li>Messages sent only with explicit opt-in consent</li>
            <li>Compliance with WhatsApp Business Policy</li>
            <li>Easy opt-out by replying &ldquo;STOP&rdquo;</li>
          </ul>
          <p className="mb-2"><strong>Google Compliance:</strong></p>
          <ul className="list-disc space-y-1 pl-6">
            <li>Google Analytics 4 with enhanced privacy settings</li>
            <li>Google Ads policies compliance</li>
            <li>Consent mode implementation</li>
          </ul>
        </Section>

        <Section title="11. International Data Transfers">
          <p>
            Your data may be transferred to and processed in the United States where our
            servers are located. We ensure appropriate safeguards are in place for any
            international transfers in compliance with applicable laws.
          </p>
        </Section>

        <Section title="12. Children&apos;s Privacy">
          <p>
            Our services are not directed to individuals under 18. We do not knowingly
            collect personal information from children. If we become aware of data from
            anyone under 18, we will promptly delete it.
          </p>
        </Section>

        <Section title="13. Changes to This Policy">
          <p>
            We may update this Privacy Policy periodically. Material changes will be
            notified via email or prominent website notice 30 days before taking effect.
            The updated version will always be available on this page with the revision date.
          </p>
        </Section>

        <Section title="14. Contact Information">
          <p>
            For privacy-related questions, to exercise your rights, or to file a complaint,
            please contact us at{' '}
            <a href="mailto:support@botrei.com" className="text-indigo-600 hover:underline">
              support@botrei.com
            </a>.
            We respond to all privacy requests within 30 days.
          </p>
        </Section>
      </div>
    </LegalLayout>
  );
}

