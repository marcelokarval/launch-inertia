import { useCallback, useRef } from 'react';

/**
 * Minimal email validation — matches "x@y.z" pattern.
 * Not RFC-compliant; just catches obvious non-emails.
 */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Minimum digits for a phone number to be considered valid-looking */
const MIN_PHONE_DIGITS = 8;

/** Debounce interval — avoid spamming beacon on rapid blur events */
const DEBOUNCE_MS = 2000;

interface UseCaptureIntentOptions {
  captureToken: string;
}

interface UseCaptureIntentReturn {
  /** Attach to email Input's onBlur */
  handleEmailBlur: (value: string) => void;
  /** Attach to PhoneInput's onBlur (receives raw phone string) */
  handlePhoneBlur: (value: string) => void;
}

/**
 * Hook for capturing form abandonment intent.
 *
 * Sends a sendBeacon to `/api/capture-intent/` when the visitor
 * blurs out of email or phone fields with valid-looking data.
 * This captures partial form data for visitors who never submit.
 *
 * Debounced: only fires once per field per 2-second window.
 * The hints are stored server-side in the Django session for
 * pre-filling the form on return visits.
 */
export function useCaptureIntent({
  captureToken,
}: UseCaptureIntentOptions): UseCaptureIntentReturn {
  const lastEmailSent = useRef('');
  const lastPhoneSent = useRef('');
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sendIntent = useCallback(
    (emailHint: string, phoneHint: string) => {
      // Clear existing debounce
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }

      debounceTimer.current = setTimeout(() => {
        const payload = JSON.stringify({
          email_hint: emailHint,
          phone_hint: phoneHint,
          capture_token: captureToken,
        });

        try {
          if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/capture-intent/', payload);
          } else {
            fetch('/api/capture-intent/', {
              method: 'POST',
              body: payload,
              headers: { 'Content-Type': 'application/json' },
              keepalive: true,
            }).catch(() => {
              // Silent — non-critical
            });
          }
        } catch {
          // Silent — non-critical
        }
      }, DEBOUNCE_MS);
    },
    [captureToken],
  );

  const handleEmailBlur = useCallback(
    (value: string) => {
      const trimmed = value.trim().toLowerCase();
      if (!trimmed || trimmed === lastEmailSent.current) return;
      if (!EMAIL_REGEX.test(trimmed)) return;

      lastEmailSent.current = trimmed;
      sendIntent(trimmed, '');
    },
    [sendIntent],
  );

  const handlePhoneBlur = useCallback(
    (value: string) => {
      const digits = value.replace(/\D/g, '');
      if (digits.length < MIN_PHONE_DIGITS) return;
      if (value === lastPhoneSent.current) return;

      lastPhoneSent.current = value;
      sendIntent('', value);
    },
    [sendIntent],
  );

  return { handleEmailBlur, handlePhoneBlur };
}
