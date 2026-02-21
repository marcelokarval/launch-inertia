import { Head, usePage } from '@inertiajs/react';

import CaptureLayout from '@/layouts/CaptureLayout';
import CaptureForm from '@/components/CaptureForm';
import type { CapturePageProps, HeadlinePart, SharedProps } from '@/types';

/**
 * Capture/Index — Lead capture landing page.
 *
 * Dark theme, left-aligned, red accent highlights.
 * Visual parity with legacy inscrever-wh-rc-v3-layout.tsx.
 * All data comes from Django as Inertia props (campaign JSON fixture).
 * FingerprintJS config comes from shared props (InertiaShareMiddleware).
 */
export default function CaptureIndex({
  campaign,
  capture_token,
  prefill,
  errors,
}: CapturePageProps) {
  const { fingerprint } = usePage<{ fingerprint?: SharedProps['fingerprint'] }>().props;
  const { headline, subheadline, badges, form, trust_badge, social_proof, meta } =
    campaign;

  return (
    <CaptureLayout backgroundImage={campaign.background_image}>
      <Head title={meta.title} />

      <div className="space-y-1 md:space-y-4">
        {/* Headline — left-aligned, large, white text */}
        {headline.parts.length > 0 && headline.parts[0]?.text && (
          <div className="text-left">
            <h1 className="text-[2.125rem] font-semibold leading-tight text-white md:text-[2.375rem]">
              {headline.parts.map((part: HeadlinePart, i: number) => (
                <HeadlineSegment
                  key={i}
                  part={part}
                  highlightColor={campaign.highlight_color}
                />
              ))}
            </h1>
          </div>
        )}

        {/* Subheadline (optional) */}
        {subheadline && (
          <h2 className="text-left text-sm leading-relaxed text-white/90 min-[400px]:text-sm md:text-base">
            {subheadline}
          </h2>
        )}

        {/* Badges */}
        {badges.filter((b) => b.visible).length > 0 && (
          <div className="flex flex-wrap justify-between gap-2">
            {badges
              .filter((b) => b.visible)
              .map((badge, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 rounded-md bg-white/10 px-3 py-1.5 text-[0.8125rem] font-medium text-white/80 backdrop-blur-sm"
                >
                  <BadgeIcon icon={badge.icon} />
                  {badge.text}
                </span>
              ))}
          </div>
        )}

        {/* Social proof */}
        {social_proof.enabled && social_proof.value && (
          <p className="text-left text-sm text-white/70">
            <span className="font-semibold text-[var(--color-brand-highlight)]">
              {social_proof.value}
            </span>{' '}
            {social_proof.label}
          </p>
        )}

        {/* Capture form — negative margin to bleed on mobile like legacy */}
        <div className="-mx-5 pt-2 md:mx-0">
          <CaptureForm
            campaignSlug={campaign.slug}
            formConfig={form}
            fingerprintApiKey={fingerprint?.api_key ?? ''}
            fingerprintEndpoint={fingerprint?.endpoint || undefined}
            captureToken={capture_token}
            prefill={prefill}
            serverErrors={errors}
          />
        </div>

        {/* Trust badge */}
        {trust_badge.enabled && (
          <div className="pt-2">
            <p className="flex items-center gap-1.5 text-xs text-white/50">
              <TrustIcon icon={trust_badge.icon} />
              {trust_badge.text}
            </p>
          </div>
        )}
      </div>
    </CaptureLayout>
  );
}

/**
 * Headline segment renderer — matches legacy highlight patterns.
 *
 * - 'highlight' + color='red': red background pill (#FB061A) with white text
 * - 'highlight' + color='white': plain white text
 * - 'highlight' (default): uses brand highlight color as text color
 * - 'underline': underlined text
 * - 'normal': plain text
 */
function HeadlineSegment({
  part,
  highlightColor,
}: {
  part: HeadlinePart;
  highlightColor?: string;
}) {
  if (part.type === 'highlight') {
    if (part.color === 'red') {
      return (
        <span
          className="inline px-1 py-0.5"
          style={{ backgroundColor: highlightColor || '#FB061A' }}
        >
          <span className="text-white" style={{ lineHeight: '1.5' }}>
            {part.text}
          </span>
        </span>
      );
    }
    if (part.color === 'white') {
      return <span className="text-white">{part.text}</span>;
    }
    // Default highlight — brand color text
    return (
      <span style={{ color: highlightColor || 'var(--color-brand-highlight)' }}>
        {part.text}
      </span>
    );
  }

  if (part.type === 'underline') {
    return <span className="underline decoration-2">{part.text}</span>;
  }

  // Normal text — check for extra bold pattern
  if (part.text?.includes('por uma fração do valor')) {
    return <span className="font-extrabold">{part.text}</span>;
  }

  return <span>{part.text}</span>;
}

/** Icon resolver for campaign badges. */
function BadgeIcon({ icon }: { icon: string }) {
  const iconMap: Record<string, string> = {
    calendar: '\u{1F4C5}',
    clock: '\u{23F0}',
    trophy: '\u{1F3C6}',
    star: '\u{2B50}',
    check: '\u{2705}',
    youtube: '\u{1F4BB}',
  };
  return <span aria-hidden="true">{iconMap[icon] || '\u{2022}'}</span>;
}

/** Icon resolver for trust badges. */
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
