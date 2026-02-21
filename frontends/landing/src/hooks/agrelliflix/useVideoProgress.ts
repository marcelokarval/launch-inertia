import { useState, useEffect, useCallback } from 'react';

import type {
  AgrelliflixEpisode,
  ProgressRecord,
  UseVideoProgressReturn,
  VideoProgress,
} from '@/types';

const STORAGE_KEY = 'agrelliflix_progress';

/**
 * Video progress tracking via localStorage.
 *
 * Tracks watched seconds, completion percentage, and last-watched date
 * for each episode. Considers an episode completed at 95%.
 */
export function useVideoProgress(): UseVideoProgressReturn {
  const [progress, setProgress] = useState<ProgressRecord>({});

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    try {
      setProgress(JSON.parse(stored) as ProgressRecord);
    } catch {
      // Corrupted data — start fresh
    }
  }, []);

  const saveProgress = useCallback(
    (episodeId: number, watchedSeconds: number, totalSeconds: number): boolean => {
      const percentage = totalSeconds > 0 ? (watchedSeconds / totalSeconds) * 100 : 0;
      const completed = percentage >= 95;

      const entry: VideoProgress = {
        episodeId,
        watchedSeconds,
        totalSeconds,
        percentage,
        lastWatchedAt: new Date().toISOString(),
        completed,
      };

      setProgress((prev) => {
        const updated = { ...prev, [episodeId]: entry };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

        window.dispatchEvent(
          new CustomEvent('videoProgressUpdate', {
            detail: { episodeId, progress: entry },
          }),
        );

        return updated;
      });

      return completed;
    },
    [],
  );

  const getEpisodeProgress = useCallback(
    (episodeId: number): VideoProgress | null => progress[episodeId] ?? null,
    [progress],
  );

  const getOverallProgress = useCallback((): number => {
    const entries = Object.values(progress);
    if (entries.length === 0) return 0;
    return entries.reduce((sum, ep) => sum + ep.percentage, 0) / entries.length;
  }, [progress]);

  const hasWatchedAll = useCallback(
    (totalEpisodes: number): boolean => {
      return Object.values(progress).filter((p) => p.completed).length === totalEpisodes;
    },
    [progress],
  );

  const getNextEpisode = useCallback(
    (episodes: AgrelliflixEpisode[]): AgrelliflixEpisode | null => {
      for (const episode of episodes) {
        const ep = progress[episode.id];
        if (!ep || !ep.completed) return episode;
      }
      return null;
    },
    [progress],
  );

  const resetProgress = useCallback(() => {
    setProgress({});
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    progress,
    saveProgress,
    getEpisodeProgress,
    getOverallProgress,
    hasWatchedAll,
    getNextEpisode,
    resetProgress,
  };
}
