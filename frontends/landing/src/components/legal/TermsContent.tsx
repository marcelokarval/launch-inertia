import Section from '@/components/legal/Section';

/**
 * Terms of Service content — reusable without layout wrapper.
 *
 * Used in both the /terms/ page and the LegalModal.
 */
export default function TermsContent() {
  return (
    <div className="space-y-6 text-sm leading-relaxed text-gray-300">
      {/* NO REFUND NOTICE */}
      <div className="rounded-lg border border-red-600/50 bg-red-900/20 p-4">
        <h3 className="mb-2 text-lg font-bold text-red-400">
          IMPORTANT: NO REFUND POLICY
        </h3>
        <p className="text-sm font-semibold text-white">
          This is a digital subscription service with immediate access to
          content. NO REFUNDS are available after your subscription is activated.
          You may cancel future billing at any time.
        </p>
      </div>

      <Section title="1. Acceptance of Terms">
        <p>
          By accessing or using our services, you agree to be bound by these
          Terms of Service and all applicable laws and regulations. If you do not
          agree with any of these terms, you are prohibited from using or
          accessing this site. You must be at least 18 years old to use our
          services.
        </p>
      </Section>

      <Section title="2. Subscription Service Description">
        <p className="mb-2">
          We provide a subscription-based educational platform offering:
        </p>
        <ul className="list-disc space-y-1 pl-6">
          <li>Unlimited access to our digital educational content library</li>
          <li>Exclusive community access via WhatsApp and other platforms</li>
          <li>Regular content updates and new materials</li>
          <li>Live sessions and webinars (when available)</li>
          <li>24/7 access to all subscribed content</li>
        </ul>
      </Section>

      <Section title="3. Billing and Payment Terms">
        <p className="mb-2">
          <strong>Subscription Billing:</strong>
        </p>
        <ul className="mb-3 list-disc space-y-1 pl-6">
          <li>All prices are in US Dollars (USD)</li>
          <li>
            Subscriptions automatically renew monthly/annually unless cancelled
          </li>
          <li>Payment is charged at the beginning of each billing period</li>
          <li>We accept payment via credit/debit cards through Stripe</li>
          <li>
            You authorize us to charge your payment method on a recurring basis
          </li>
        </ul>
        <p>
          <strong>Price Changes:</strong> We reserve the right to modify
          subscription fees. You will receive 30 days advance notice of any
          price increases.
        </p>
      </Section>

      <Section title="4. No Refund Policy">
        <p className="mb-2">
          <strong>Digital Product — No Refunds:</strong>
        </p>
        <ul className="list-disc space-y-1 pl-6">
          <li>
            Due to immediate access to our digital content library upon
            subscription, NO REFUNDS are available once your subscription is
            activated
          </li>
          <li>
            Free trials (if offered) can be cancelled before converting to paid
            subscription
          </li>
          <li>
            Cancellation stops future charges but does not refund the current
            billing period
          </li>
          <li>
            You retain access to content until the end of your current paid
            period
          </li>
          <li>Chargebacks may result in immediate account termination</li>
        </ul>
      </Section>

      <Section title="5. Cancellation Policy (FTC Compliance)">
        <p className="mb-2">
          <strong>Easy Cancellation &mdash; &ldquo;Click to Cancel&rdquo;:</strong>
        </p>
        <ul className="list-disc space-y-1 pl-6">
          <li>Cancel anytime through your account dashboard with one click</li>
          <li>No questions asked cancellation policy</li>
          <li>Immediate email confirmation of cancellation</li>
          <li>Access continues until the end of current billing period</li>
          <li>No cancellation fees or penalties</li>
          <li>Re-subscribe anytime after cancellation</li>
        </ul>
      </Section>

      <Section title="6. Account Registration and Security">
        <p>
          You agree to: (a) provide accurate, current, and complete information;
          (b) maintain and update your information; (c) maintain the security of
          your password and account; (d) notify us immediately of any
          unauthorized use; (e) accept responsibility for all activities under
          your account.
        </p>
      </Section>

      <Section title="7. Intellectual Property Rights">
        <p>
          All content on this platform, including but not limited to text,
          graphics, logos, images, audio clips, video, data, and software, is
          our property or licensed to us and is protected by United States and
          international copyright laws. You may not reproduce, distribute,
          modify, or create derivative works without written permission.
        </p>
      </Section>

      <Section title="8. Prohibited Uses">
        <p className="mb-2">You agree NOT to:</p>
        <ul className="list-disc space-y-1 pl-6">
          <li>Share your account credentials or subscription access</li>
          <li>
            Download, copy, or redistribute our content without permission
          </li>
          <li>Use our content for commercial purposes</li>
          <li>Attempt to bypass any security measures</li>
          <li>Use automated systems to access our services</li>
          <li>Violate any applicable laws or regulations</li>
          <li>Infringe upon intellectual property rights</li>
        </ul>
      </Section>

      <Section title="9. Disclaimer of Warranties">
        <p>
          THE SERVICES ARE PROVIDED &ldquo;AS IS&rdquo; AND &ldquo;AS
          AVAILABLE&rdquo; WITHOUT WARRANTIES OF ANY KIND. WE DO NOT GUARANTEE
          SPECIFIC RESULTS OR SUCCESS. Educational content is for informational
          purposes only and does not constitute professional advice.
        </p>
      </Section>

      <Section title="10. Limitation of Liability">
        <p>
          TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE SHALL NOT BE LIABLE FOR ANY
          INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR
          ANY LOSS OF PROFITS OR REVENUES. OUR TOTAL LIABILITY SHALL NOT EXCEED
          THE AMOUNT YOU PAID FOR THE SERVICES IN THE PAST TWELVE MONTHS.
        </p>
      </Section>

      <Section title="11. Arbitration Agreement">
        <p>
          Any dispute arising from these Terms shall be resolved through binding
          arbitration under the American Arbitration Association rules rather
          than in court, except that you may assert claims in small claims
          court. You waive your right to participate in class actions.
        </p>
      </Section>

      <Section title="12. Governing Law">
        <p>
          These Terms shall be governed by and construed in accordance with the
          laws of the United States and the State of Delaware, without regard to
          its conflict of law provisions.
        </p>
      </Section>

      <Section title="13. Platform Compliance">
        <p>
          We comply with the terms of service of third-party platforms including
          Meta (Facebook/Instagram), WhatsApp Business API, Google Ads, and
          Stripe.
        </p>
      </Section>

      <Section title="14. Modifications to Terms">
        <p>
          We reserve the right to modify these terms at any time. Material
          changes will be notified via email or prominent notice on our website
          30 days before taking effect.
        </p>
      </Section>

      <Section title="15. Contact Information">
        <p>
          For questions about these Terms of Service, please contact us at{' '}
          <a
            href="mailto:support@botrei.com"
            className="text-red-400 hover:underline"
          >
            support@botrei.com
          </a>
          .
        </p>
      </Section>
    </div>
  );
}
