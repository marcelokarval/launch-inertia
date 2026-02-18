import { useCallback, useState } from 'react';

import type { FingerprintResult } from '@/types';

/**
 * Hook that manages FingerprintJS Pro state for capture forms.
 *
 * Returns:
 *  - fpResult: resolved FingerprintResult or null
 *  - visitorId: shortcut to fpResult.visitorId or ""
 *  - requestId: shortcut to fpResult.requestId or ""
 *  - handleFingerprintResult: callback to pass to FingerprintProvider
 *  - isReady: true once fingerprint has resolved
 */
export function useFingerprint() {
  const [fpResult, setFpResult] = useState<FingerprintResult | null>(null);

  const handleFingerprintResult = useCallback((result: FingerprintResult) => {
    setFpResult(result);
  }, []);

  return {
    fpResult,
    visitorId: fpResult?.visitorId ?? '',
    requestId: fpResult?.requestId ?? '',
    isReady: fpResult !== null,
    handleFingerprintResult,
  };
}
