import { useEffect, useRef, type ReactNode } from 'react';
import {
  FpjsProvider,
  CacheLocation,
} from '@fingerprintjs/fingerprintjs-pro-react';

import type { FingerprintResult } from '@/types';

// ── Constants ──────────────────────────────────────────────────────────

/** Cookie name that Django VisitorMiddleware reads on every request */
const FPJS_VID_COOKIE = 'fpjs_vid';

/** Cookie TTL: 365 days (matches converted session TTL) */
const COOKIE_MAX_AGE_DAYS = 365;

/** In-memory cache duration: 24 hours */
const CACHE_TIME_SECONDS = 60 * 60 * 24;

/** Custom subdomain proxy — avoids ad blockers */
const DEFAULT_ENDPOINT = 'https://finger.arthuragrelli.com';

/** CDN fallback when custom proxy is unreachable */
const FALLBACK_ENDPOINT = 'https://fpjs.pro';

// ── Cookie helpers ─────────────────────────────────────────────────────

function setCookie(name: string, value: string, days: number): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires};path=/;SameSite=Lax`;
}

/**
 * Send fingerprint result to Django via sendBeacon (fire-and-forget).
 *
 * This ensures that even if the visitor bounces after a single page view,
 * Django links the FingerprintIdentity to the session Identity and
 * retroactively updates the PAGE_VIEW CaptureEvent with visitor_id.
 *
 * Falls back to fetch() with keepalive if sendBeacon is unavailable.
 */
function sendFpBeacon(result: FingerprintResult, captureToken?: string): void {
  const payload = JSON.stringify({
    visitor_id: result.visitorId,
    request_id: result.requestId,
    confidence: result.confidence,
    capture_token: captureToken || '',
  });

  try {
    if (navigator.sendBeacon) {
      // sendBeacon sends as text/plain — Django view handles this
      const sent = navigator.sendBeacon('/api/fp-resolve/', payload);
      if (!sent) {
        // Queue full — fallback to fetch
        fetchFallback(payload);
      }
    } else {
      fetchFallback(payload);
    }
  } catch {
    // Beacon/fetch failure is non-critical — Django middleware
    // will link FP on the next request via cookie anyway
  }
}

function fetchFallback(payload: string): void {
  fetch('/api/fp-resolve/', {
    method: 'POST',
    body: payload,
    headers: { 'Content-Type': 'application/json' },
    keepalive: true,
  }).catch(() => {
    // Silent failure — non-critical
  });
}

// ── Eager loader (runs ASAP on mount) ──────────────────────────────────

interface EagerLoaderProps {
  apiKey: string;
  endpoint: string;
  /** Called once the SDK resolves. Sets cookie + window.fpResult. */
  onResult: (result: FingerprintResult) => void;
  /** Capture token from the page load (for retroactive event update) */
  captureToken?: string;
}

/**
 * Loads FingerprintJS Pro SDK eagerly (outside React render cycle).
 *
 * Does NOT use the React hook — uses the raw JS agent for maximum speed.
 * The hook (useVisitorData) is still available via FpjsProvider for
 * components that need fresh data.
 *
 * Sets:
 *  - cookie `fpjs_vid` (Django reads on next request)
 *  - window.fpResult (global sync for backward compat)
 *  - dispatches CustomEvent 'fingerprint-ready'
 */
function FingerprintEagerLoader({ apiKey, endpoint, onResult, captureToken }: EagerLoaderProps) {
  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current || window.__fpLoaderStarted) return;
    hasStarted.current = true;
    window.__fpLoaderStarted = true;

    const startTime = performance.now();

    async function load() {
      try {
        const FingerprintJS = await import('@fingerprintjs/fingerprintjs-pro');
        const fp = await FingerprintJS.load({
          apiKey,
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

        // 1. Set cookie for Django middleware (next request)
        setCookie(FPJS_VID_COOKIE, result.visitorId, COOKIE_MAX_AGE_DAYS);

        // 2. Global sync (window)
        window.fpResult = result;

        // 3. CustomEvent for any listener
        window.dispatchEvent(
          new CustomEvent('fingerprint-ready', { detail: result }),
        );

        // 4. Callback to parent
        onResult(result);

        // 5. Beacon to Django — links FP to session identity + updates PAGE_VIEW
        sendFpBeacon(result, captureToken);
      } catch (err) {
        console.warn('[FingerprintJS] Failed to load:', err);
        window.fpResult = undefined;
      }
    }

    load();
  }, [apiKey, endpoint, onResult, captureToken]);

  return null;
}

// ── Public API ─────────────────────────────────────────────────────────

interface FingerprintProviderProps {
  apiKey: string;
  /** Custom endpoint (proxy subdomain). Falls back to DEFAULT_ENDPOINT. */
  endpoint?: string;
  /** Called when fingerprint resolves (visitorId, requestId) */
  onResult: (result: FingerprintResult) => void;
  /** Capture token from Django (for retroactive PAGE_VIEW update via beacon) */
  captureToken?: string;
  children?: ReactNode;
}

/**
 * FingerprintJS Pro provider for landing pages.
 *
 * Wraps children with FpjsProvider (for useVisitorData access) and
 * immediately fires the eager loader to resolve the visitor ASAP.
 *
 * When apiKey is empty, renders children only (no-op).
 *
 * Sets cookie `fpjs_vid` so Django VisitorMiddleware can resolve
 * FingerprintIdentity on the next request.
 */
export default function FingerprintProvider({
  apiKey,
  endpoint,
  onResult,
  captureToken,
  children,
}: FingerprintProviderProps) {
  if (!apiKey) {
    return <>{children}</>;
  }

  const resolvedEndpoint = endpoint || DEFAULT_ENDPOINT;

  return (
    <FpjsProvider
      loadOptions={{
        apiKey,
        endpoint: [resolvedEndpoint, FALLBACK_ENDPOINT],
      }}
      cacheLocation={CacheLocation.Memory}
      cacheTimeInSeconds={CACHE_TIME_SECONDS}
      cachePrefix="fp_cache_"
    >
      <FingerprintEagerLoader
        apiKey={apiKey}
        endpoint={resolvedEndpoint}
        onResult={onResult}
        captureToken={captureToken}
      />
      {children}
    </FpjsProvider>
  );
}

// Re-export hook for components that need fresh data
export { useVisitorData } from '@fingerprintjs/fingerprintjs-pro-react';
