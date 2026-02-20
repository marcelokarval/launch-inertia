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
 * Each field has its own debounce timer so blurring email then phone
 * within the debounce window sends BOTH beacons instead of cancelling
 * the first one. Each beacon sends all accumulated hints (not just
 * the field that triggered it) so the server always has the latest state.
 */
export function useCaptureIntent({
  captureToken,
}: UseCaptureIntentOptions): UseCaptureIntentReturn {
  const lastEmailSent = useRef('');
  const lastPhoneSent = useRef('');
  const currentEmail = useRef('');
  const currentPhone = useRef('');
  const emailTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const phoneTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sendIntent = useCallback(
    (emailHint: string, phoneHint: string) => {
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
    },
    [captureToken],
  );

  const handleEmailBlur = useCallback(
    (value: string) => {
      const trimmed = value.trim().toLowerCase();
      if (!trimmed || trimmed === lastEmailSent.current) return;
      if (!EMAIL_REGEX.test(trimmed)) return;

      currentEmail.current = trimmed;

      // Clear only the email timer (phone timer runs independently)
      if (emailTimer.current) {
        clearTimeout(emailTimer.current);
      }

      emailTimer.current = setTimeout(() => {
        lastEmailSent.current = trimmed;
        // Send both accumulated hints so server has full state
        sendIntent(trimmed, currentPhone.current);
      }, DEBOUNCE_MS);
    },
    [sendIntent],
  );

  const handlePhoneBlur = useCallback(
    (value: string) => {
      const digits = value.replace(/\D/g, '');
      if (digits.length < MIN_PHONE_DIGITS) return;
      if (value === lastPhoneSent.current) return;

      currentPhone.current = value;

      // Clear only the phone timer (email timer runs independently)
      if (phoneTimer.current) {
        clearTimeout(phoneTimer.current);
      }

      phoneTimer.current = setTimeout(() => {
        lastPhoneSent.current = value;
        // Send both accumulated hints so server has full state
        sendIntent(currentEmail.current, value);
      }, DEBOUNCE_MS);
    },
    [sendIntent],
  );

  return { handleEmailBlur, handlePhoneBlur };
}
