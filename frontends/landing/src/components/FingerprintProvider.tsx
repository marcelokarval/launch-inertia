import { useEffect, useRef } from 'react';

interface FingerprintProviderProps {
  apiKey: string;
  onResult: (visitorId: string, requestId: string) => void;
}

/**
 * FingerprintJS Pro integration.
 *
 * Loads the FingerprintJS Pro agent and resolves the visitor ID.
 * The result is passed to the parent via onResult callback,
 * which should populate the form's hidden fields.
 *
 * If the API key is empty, the component is a no-op.
 */
export default function FingerprintProvider({
  apiKey,
  onResult,
}: FingerprintProviderProps) {
  const hasLoaded = useRef(false);

  useEffect(() => {
    if (!apiKey || hasLoaded.current) return;
    hasLoaded.current = true;

    async function loadFingerprint() {
      try {
        // Uses the open-source FingerprintJS library.
        // The Pro version (with requestId) requires a paid API key
        // and the @fingerprintjs/fingerprintjs-pro package.
        const FingerprintJS = await import('@fingerprintjs/fingerprintjs');
        const fp = await FingerprintJS.load();
        const result = await fp.get();

        // Open-source version only provides visitorId.
        // requestId is generated client-side as a unique identifier.
        const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        onResult(result.visitorId, requestId);
      } catch (err) {
        // Fingerprint failure is non-critical — form still works
        console.warn('FingerprintJS failed to load:', err);
      }
    }

    loadFingerprint();
  }, [apiKey, onResult]);

  return null;
}
