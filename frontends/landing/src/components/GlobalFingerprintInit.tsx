/**
 * App-level fingerprint initializer.
 *
 * Loads FingerprintJS Pro SDK once on first page load (any page) and:
 *   1. Sets `fpjs_vid` cookie (Django VisitorMiddleware reads on next request)
 *   2. Sets `window.fpResult` (global sync)
 *   3. Dispatches `fingerprint-ready` CustomEvent
 *   4. Sends beacon to Django to link fingerprint to session identity
 *
 * Uses `window.__fpLoaderStarted` guard to prevent double-loading
 * if CaptureForm's FingerprintProvider mounts on the same page.
 *
 * Reads `fingerprint.api_key` and `fingerprint.endpoint` from Inertia
 * shared props (injected by InertiaShareMiddleware).
 */
import { useEffect, useRef } from 'react';
import { usePage } from '@inertiajs/react';

import type { FingerprintResult, SharedProps } from '@/types';

const FPJS_VID_COOKIE = 'fpjs_vid';
const COOKIE_MAX_AGE_DAYS = 365;
const DEFAULT_ENDPOINT = 'https://finger.arthuragrelli.com';
const FALLBACK_ENDPOINT = 'https://fpjs.pro';

function setCookie(name: string, value: string, days: number): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires};path=/;SameSite=Lax`;
}

function getCookie(name: string): string {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : '';
}

function sendBeaconToServer(result: FingerprintResult): void {
  const payload = JSON.stringify({
    visitor_id: result.visitorId,
    request_id: result.requestId,
    confidence: result.confidence,
    capture_token: '',
  });

  try {
    if (navigator.sendBeacon) {
      const sent = navigator.sendBeacon('/api/fp-resolve/', payload);
      if (!sent) {
        fetch('/api/fp-resolve/', {
          method: 'POST',
          body: payload,
          headers: { 'Content-Type': 'application/json' },
          keepalive: true,
        }).catch(() => {});
      }
    } else {
      fetch('/api/fp-resolve/', {
        method: 'POST',
        body: payload,
        headers: { 'Content-Type': 'application/json' },
        keepalive: true,
      }).catch(() => {});
    }
  } catch {
    // Non-critical — Django middleware links FP via cookie on next request
  }
}

export default function GlobalFingerprintInit() {
  const { fingerprint } = usePage().props as SharedProps;
  const hasStarted = useRef(false);

  useEffect(() => {
    // No API key configured — skip
    if (!fingerprint?.api_key) return;

    // Already started by this component or CaptureForm's FingerprintProvider
    if (hasStarted.current || window.__fpLoaderStarted) return;

    // Cookie already set from a previous visit — no need to call API again.
    // Django middleware will use the existing cookie.
    // But we still need window.fpResult for in-page consumers.
    const existingVid = getCookie(FPJS_VID_COOKIE);
    if (existingVid) {
      // Populate window.fpResult from cookie (minimal — no confidence data)
      if (!window.fpResult) {
        window.fpResult = {
          visitorId: existingVid,
          requestId: '',
          confidence: { score: 0 },
          visitorFound: true,
          loadedAt: Date.now(),
          loadTime: 0,
        };
        window.dispatchEvent(
          new CustomEvent('fingerprint-ready', { detail: window.fpResult }),
        );
      }
      return;
    }

    hasStarted.current = true;
    window.__fpLoaderStarted = true;

    const startTime = performance.now();
    const endpoint = fingerprint.endpoint || DEFAULT_ENDPOINT;

    async function load() {
      try {
        const FingerprintJS = await import('@fingerprintjs/fingerprintjs-pro');
        const fp = await FingerprintJS.load({
          apiKey: fingerprint!.api_key,
          endpoint: [endpoint, FALLBACK_ENDPOINT],
        });
        const data = await fp.get();

        const result: FingerprintResult = {
          visitorId: data.visitorId,
          requestId: data.requestId,
          confidence: data.confidence,
          visitorFound: data.visitorFound,
          loadedAt: Date.now(),
          loadTime: Math.round(performance.now() - startTime),
        };

        // 1. Cookie for Django middleware
        setCookie(FPJS_VID_COOKIE, result.visitorId, COOKIE_MAX_AGE_DAYS);

        // 2. Global sync
        window.fpResult = result;

        // 3. Event for listeners (useFingerprint hook)
        window.dispatchEvent(
          new CustomEvent('fingerprint-ready', { detail: result }),
        );

        // 4. Beacon to Django
        sendBeaconToServer(result);
      } catch (err) {
        console.warn('[GlobalFingerprintInit] Failed to load:', err);
      }
    }

    load();
  }, [fingerprint]);

  return null;
}
