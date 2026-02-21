import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';

import type { AgrelliflixAchievement, UseAchievementsReturn } from '@/types';

/**
 * Achievement system hook.
 *
 * Manages unlocked achievements and shows toast notifications
 * when a new achievement is earned. Achievement definitions
 * come from the campaign config.
 */
export function useAchievements(
  achievementsConfig: Record<string, AgrelliflixAchievement> = {},
): UseAchievementsReturn {
  const [achievements, setAchievements] = useState<string[]>([]);

  const unlockAchievement = useCallback(
    (id: string) => {
      setAchievements((prev) => {
        if (prev.includes(id)) return prev;

        const config = achievementsConfig[id];
        if (config) {
          toast.success(`${config.icon || '🏆'} Conquista Desbloqueada: ${config.title}!`, {
            duration: 5000,
            style: {
              background: '#1F1F1F',
              color: '#FFD700',
              border: '1px solid #FFD700',
            },
          });
        }

        return [...prev, id];
      });
    },
    [achievementsConfig],
  );

  const hasAchievement = useCallback(
    (id: string) => achievements.includes(id),
    [achievements],
  );

  return { achievements, unlockAchievement, hasAchievement };
}
