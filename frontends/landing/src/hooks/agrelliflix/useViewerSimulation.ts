import { useState, useEffect } from 'react';

import type { UseViewerSimulationReturn } from '@/types';

interface UseViewerSimulationOptions {
  initialCount?: number;
  minCount?: number;
  maxCount?: number;
  updateInterval?: number;
  maxChange?: number;
}

/**
 * Fake viewer count simulation for social proof.
 *
 * Generates a fluctuating viewer count around the initial value.
 * Config values come from the campaign JSON `social_proof` section.
 */
export function useViewerSimulation(
  options: UseViewerSimulationOptions = {},
): UseViewerSimulationReturn {
  const {
    initialCount = 1247,
    minCount = 800,
    maxCount = 2000,
    updateInterval = 5000,
    maxChange = 50,
  } = options;

  const [currentViewers, setCurrentViewers] = useState(initialCount);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentViewers((prev) => {
        const change = Math.floor(Math.random() * maxChange) - maxChange / 2;
        const next = prev + change;
        return Math.max(minCount, Math.min(maxCount, next));
      });
    }, updateInterval);

    return () => clearInterval(interval);
  }, [minCount, maxCount, updateInterval, maxChange]);

  return { currentViewers };
}
