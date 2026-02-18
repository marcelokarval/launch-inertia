/// <reference types="vite/client" />

import type { FingerprintResult } from '@/types';

declare global {
  interface Window {
    /** FingerprintJS Pro result — set by FingerprintProvider on load */
    fpResult?: FingerprintResult;
    /** Guard: true once the FP eager loader has started */
    __fpLoaderStarted?: boolean;
  }
}
