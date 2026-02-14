import { Head } from '@inertiajs/react';

import CaptureLayout from '@/layouts/CaptureLayout';
import CaptureForm from '@/components/CaptureForm';
import type { CapturePageProps, HeadlinePart } from '@/types';

/**
 * Capture/Index — Lead capture landing page.
 *
 * Renders campaign headline, badges, capture form, and trust indicators.
 * All data comes from Django as Inertia props (campaign JSON fixture).
 */
export default function CaptureIndex({
  campaign,
  fingerprint_api_key,
  errors,
}: CapturePageProps) {
  const { headline, badges, form, trust_badge, social_proof, meta } = campaign;

  return (
    <CaptureLayout>
      <Head title={meta.title} />

      <div className="rounded-2xl bg-[var(--color-surface)] p-6 shadow-2xl sm:p-8">
        {/* Headline */}
        <h1 className="mb-4 text-center text-2xl font-bold leading-tight text-[var(--color-text-primary)] sm:text-3xl">
          {headline.parts.map((part: HeadlinePart, i: number) =>
            part.type === 'highlight' ? (
              <span
                key={i}
                className="text-[var(--color-brand-primary)]"
              >
                {part.text}
              </span>
            ) : (
              <span key={i}>{part.text}</span>
            ),
          )}
        </h1>

        {/* Badges */}
        {badges.length > 0 && (
          <div className="mb-6 flex flex-wrap justify-center gap-3">
            {badges
              .filter((b) => b.visible)
              .map((badge, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-brand-primary)]/10 px-3 py-1 text-xs font-medium text-[var(--color-brand-primary)]"
                >
                  <BadgeIcon icon={badge.icon} />
                  {badge.text}
                </span>
              ))}
          </div>
        )}

        {/* Social proof */}
        {social_proof.enabled && social_proof.value && (
          <p className="mb-6 text-center text-sm text-[var(--color-text-secondary)]">
            <span className="font-semibold text-[var(--color-brand-primary)]">
              {social_proof.value}
            </span>{' '}
            {social_proof.label}
          </p>
        )}

        {/* Capture form */}
        <CaptureForm
          campaignSlug={campaign.slug}
          formConfig={form}
          fingerprintApiKey={fingerprint_api_key}
          serverErrors={errors}
        />

        {/* Trust badge */}
        {trust_badge.enabled && (
          <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-[var(--color-text-muted)]">
            <TrustIcon icon={trust_badge.icon} />
            {trust_badge.text}
          </p>
        )}
      </div>
    </CaptureLayout>
  );
}

/** Simple icon resolver for badges. */
function BadgeIcon({ icon }: { icon: string }) {
  const iconMap: Record<string, string> = {
    calendar: '\u{1F4C5}',
    clock: '\u{23F0}',
    trophy: '\u{1F3C6}',
    star: '\u{2B50}',
    check: '\u{2705}',
  };
  return <span aria-hidden="true">{iconMap[icon] || '\u{2022}'}</span>;
}

/** Simple icon resolver for trust badges. */
function TrustIcon({ icon }: { icon: string }) {
  if (icon === 'shield') {
    return (
      <svg
        className="h-3.5 w-3.5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
        />
      </svg>
    );
  }
  return (
    <svg
      className="h-3.5 w-3.5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
      />
    </svg>
  );
}
