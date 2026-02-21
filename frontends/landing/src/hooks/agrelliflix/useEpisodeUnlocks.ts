import { useState, useEffect, useCallback, useRef } from 'react';

import type {
  AgrelliflixEpisode,
  ProgressRecord,
  UseEpisodeUnlocksReturn,
} from '@/types';

/**
 * Episode unlock logic.
 *
 * Episode 1 is always unlocked. Subsequent episodes unlock when:
 * - Their `available_at` date has passed (time-based), OR
 * - The previous episode is completed (progress-based).
 *
 * Re-checks every 60 seconds for time-based unlocks.
 */
export function useEpisodeUnlocks(
  progress: ProgressRecord,
  episodes: AgrelliflixEpisode[] = [],
): UseEpisodeUnlocksReturn {
  const [unlockedEpisodes, setUnlockedEpisodes] = useState<number[]>([1]);
  const prevRef = useRef<string>('[1]');

  const checkUnlocks = useCallback(() => {
    const now = new Date();
    const unlocked: number[] = [1]; // Episode 1 always unlocked

    for (let i = 1; i < episodes.length; i++) {
      const episode = episodes[i];
      const isTimeUnlocked = now >= new Date(episode.available_at);
      const previousCompleted = progress[episodes[i - 1].id]?.completed ?? false;

      if (isTimeUnlocked || previousCompleted) {
        unlocked.push(episode.id);
      }
    }

    // Only update state if changed (avoid re-render loops)
    const key = JSON.stringify(unlocked);
    if (key !== prevRef.current) {
      prevRef.current = key;
      setUnlockedEpisodes(unlocked);
    }
  }, [progress, episodes]);

  useEffect(() => {
    checkUnlocks();
    const interval = setInterval(checkUnlocks, 60_000);
    return () => clearInterval(interval);
  }, [checkUnlocks]);

  const isUnlocked = useCallback(
    (episodeId: number) => unlockedEpisodes.includes(episodeId),
    [unlockedEpisodes],
  );

  return { unlockedEpisodes, checkUnlocks, isUnlocked };
}
