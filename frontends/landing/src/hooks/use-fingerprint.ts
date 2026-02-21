import { useCallback, useEffect, useState } from 'react';

import type { FingerprintResult } from '@/types';

/**
 * Hook that manages FingerprintJS Pro state for capture forms.
 *
 * On mount, checks `window.fpResult` (set by GlobalFingerprintInit or
 * FingerprintProvider) for immediate sync. Also listens to the
 * `fingerprint-ready` CustomEvent for async resolution.
 *
 * Returns:
 *  - fpResult: resolved FingerprintResult or null
 *  - visitorId: shortcut to fpResult.visitorId or ""
 *  - requestId: shortcut to fpResult.requestId or ""
 *  - handleFingerprintResult: callback to pass to FingerprintProvider
 *  - isReady: true once fingerprint has resolved
 */
export function useFingerprint() {
  const [fpResult, setFpResult] = useState<FingerprintResult | null>(() => {
    // Immediate sync: GlobalFingerprintInit may have already resolved
    return window.fpResult ?? null;
  });

  const handleFingerprintResult = useCallback((result: FingerprintResult) => {
    setFpResult(result);
  }, []);

  // Listen for async resolution (GlobalFingerprintInit dispatches this event)
  useEffect(() => {
    if (fpResult) return; // Already resolved

    function onReady(e: Event) {
      const detail = (e as CustomEvent<FingerprintResult>).detail;
      if (detail) {
        setFpResult(detail);
      }
    }

    window.addEventListener('fingerprint-ready', onReady);
    return () => window.removeEventListener('fingerprint-ready', onReady);
  }, [fpResult]);

  return {
    fpResult,
    visitorId: fpResult?.visitorId ?? '',
    requestId: fpResult?.requestId ?? '',
    isReady: fpResult !== null,
    handleFingerprintResult,
  };
}
