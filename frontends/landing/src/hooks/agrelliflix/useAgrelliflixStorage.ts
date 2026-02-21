import { useState, useEffect, useCallback, useMemo } from 'react';

// ── Types ────────────────────────────────────────────────────────────

type XPLevelName = 'iniciante' | 'aprendiz' | 'expert' | 'mestre';

interface MilestonesReached {
  start: boolean;
  percent25: boolean;
  percent50: boolean;
  percent75: boolean;
  complete: boolean;
}

interface VideoProgressData {
  currentTime: number;
  duration: number;
  percentComplete: number;
  lastWatched: string;
  completed: boolean;
  milestonesReached: MilestonesReached;
}

interface GamificationData {
  xp: number;
  level: XPLevelName;
  achievements: string[];
  streakDays: number;
  lastActivity: string;
}

interface PreferencesData {
  theaterMode: boolean;
  playbackSpeed: number;
  autoplay: boolean;
  volume: number;
}

interface AgrelliflixUserData {
  videoProgress: Record<number, VideoProgressData>;
  gamification: GamificationData;
  preferences: PreferencesData;
  version: number;
  createdAt: string;
  updatedAt: string;
}

// ── Constants ────────────────────────────────────────────────────────

const STORAGE_KEY = 'agrelliflix_user_v1';
const CURRENT_VERSION = 1;

const XP_LEVELS: Record<XPLevelName, { min: number; max: number; label: string }> = {
  iniciante: { min: 0, max: 299, label: 'Iniciante' },
  aprendiz: { min: 300, max: 799, label: 'Aprendiz' },
  expert: { min: 800, max: 1499, label: 'Expert' },
  mestre: { min: 1500, max: Infinity, label: 'Mestre' },
};

const XP_REWARDS = {
  videoStart: 10,
  video25Percent: 25,
  video50Percent: 50,
  video75Percent: 75,
  videoComplete: 100,
  achievementUnlock: 50,
  dailyStreak: 30,
} as const;

const DEFAULT_DATA: AgrelliflixUserData = {
  videoProgress: {},
  gamification: {
    xp: 0,
    level: 'iniciante',
    achievements: [],
    streakDays: 0,
    lastActivity: '',
  },
  preferences: {
    theaterMode: false,
    playbackSpeed: 1,
    autoplay: true,
    volume: 1,
  },
  version: CURRENT_VERSION,
  createdAt: '',
  updatedAt: '',
};

// ── Helpers ──────────────────────────────────────────────────────────

function calculateLevel(xp: number): XPLevelName {
  if (xp >= XP_LEVELS.mestre.min) return 'mestre';
  if (xp >= XP_LEVELS.expert.min) return 'expert';
  if (xp >= XP_LEVELS.aprendiz.min) return 'aprendiz';
  return 'iniciante';
}

// ── Hook ─────────────────────────────────────────────────────────────

/**
 * Full gamification storage for AgreliFlix.
 *
 * Manages video progress with XP milestones, achievements, preferences,
 * and level progression — all persisted in localStorage.
 */
export function useAgrelliflixStorage() {
  const [data, setData] = useState<AgrelliflixUserData | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setData(JSON.parse(stored) as AgrelliflixUserData);
      } else {
        const fresh: AgrelliflixUserData = {
          ...DEFAULT_DATA,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));
        setData(fresh);
      }
    } catch {
      setData({
        ...DEFAULT_DATA,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });
    }
    setIsLoaded(true);
  }, []);

  const persist = useCallback((newData: AgrelliflixUserData) => {
    const updated = { ...newData, updatedAt: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setData(updated);
    window.dispatchEvent(
      new CustomEvent('agrelliflix_storage_update', { detail: updated }),
    );
  }, []);

  // ── Video Progress ──

  const updateVideoProgress = useCallback(
    (episodeId: number, currentTime: number, duration: number) => {
      if (!data) return undefined;

      const pct = duration > 0 ? (currentTime / duration) * 100 : 0;
      const completed = pct >= 90;
      const existing = data.videoProgress[episodeId]?.milestonesReached ?? {
        start: false,
        percent25: false,
        percent50: false,
        percent75: false,
        complete: false,
      };

      let xpGained = 0;
      const ms = { ...existing };

      if (!existing.start) { xpGained += XP_REWARDS.videoStart; ms.start = true; }
      if (pct >= 25 && !existing.percent25) { xpGained += XP_REWARDS.video25Percent; ms.percent25 = true; }
      if (pct >= 50 && !existing.percent50) { xpGained += XP_REWARDS.video50Percent; ms.percent50 = true; }
      if (pct >= 75 && !existing.percent75) { xpGained += XP_REWARDS.video75Percent; ms.percent75 = true; }
      if (completed && !existing.complete) { xpGained += XP_REWARDS.videoComplete; ms.complete = true; }

      const newXP = data.gamification.xp + xpGained;
      const newLevel = calculateLevel(newXP);

      persist({
        ...data,
        videoProgress: {
          ...data.videoProgress,
          [episodeId]: {
            currentTime,
            duration,
            percentComplete: pct,
            lastWatched: new Date().toISOString(),
            completed,
            milestonesReached: ms,
          },
        },
        gamification: {
          ...data.gamification,
          xp: newXP,
          level: newLevel,
          lastActivity: new Date().toISOString(),
        },
      });

      return { xpGained, newLevel, completed };
    },
    [data, persist],
  );

  const getVideoProgress = useCallback(
    (episodeId: number): VideoProgressData | null =>
      data?.videoProgress[episodeId] ?? null,
    [data],
  );

  const getOverallProgress = useCallback(
    (totalEpisodes: number): number => {
      if (!data) return 0;
      const done = Object.values(data.videoProgress).filter((p) => p.completed).length;
      return (done / totalEpisodes) * 100;
    },
    [data],
  );

  // ── XP System ──

  const addXP = useCallback(
    (amount: number) => {
      if (!data) return undefined;

      const newXP = data.gamification.xp + amount;
      const newLevel = calculateLevel(newXP);
      const leveledUp = newLevel !== data.gamification.level;

      persist({
        ...data,
        gamification: {
          ...data.gamification,
          xp: newXP,
          level: newLevel,
          lastActivity: new Date().toISOString(),
        },
      });

      if (leveledUp) {
        window.dispatchEvent(
          new CustomEvent('agrelliflix_level_up', {
            detail: { oldLevel: data.gamification.level, newLevel, xp: newXP },
          }),
        );
      }

      return { newXP, newLevel, leveledUp };
    },
    [data, persist],
  );

  const getLevelProgress = useCallback(() => {
    if (!data) return { current: 0, max: 300, percentage: 0, xpToNextLevel: 300 };

    const { xp, level } = data.gamification;
    const levelConfig = XP_LEVELS[level];
    const nextMin =
      level === 'mestre'
        ? xp
        : XP_LEVELS[
            level === 'iniciante'
              ? 'aprendiz'
              : level === 'aprendiz'
                ? 'expert'
                : 'mestre'
          ].min;

    const current = xp - levelConfig.min;
    const max = nextMin - levelConfig.min;
    const percentage = max > 0 ? (current / max) * 100 : 100;

    return { current, max, percentage, xpToNextLevel: nextMin - xp };
  }, [data]);

  // ── Achievements ──

  const unlockAchievement = useCallback(
    (achievementId: string) => {
      if (!data || data.gamification.achievements.includes(achievementId)) return false;

      const newXP = data.gamification.xp + XP_REWARDS.achievementUnlock;
      const newLevel = calculateLevel(newXP);

      persist({
        ...data,
        gamification: {
          ...data.gamification,
          xp: newXP,
          level: newLevel,
          achievements: [...data.gamification.achievements, achievementId],
          lastActivity: new Date().toISOString(),
        },
      });

      window.dispatchEvent(
        new CustomEvent('agrelliflix_achievement', {
          detail: { achievementId, xpGained: XP_REWARDS.achievementUnlock },
        }),
      );

      return true;
    },
    [data, persist],
  );

  const hasAchievement = useCallback(
    (achievementId: string): boolean =>
      data?.gamification.achievements.includes(achievementId) ?? false,
    [data],
  );

  // ── Preferences ──

  const updatePreference = useCallback(
    <K extends keyof PreferencesData>(key: K, value: PreferencesData[K]) => {
      if (!data) return;
      persist({ ...data, preferences: { ...data.preferences, [key]: value } });
    },
    [data, persist],
  );

  // ── Reset ──

  const resetAll = useCallback(() => {
    persist({
      ...DEFAULT_DATA,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }, [persist]);

  // ── Computed ──

  const gamification = useMemo(
    () => data?.gamification ?? DEFAULT_DATA.gamification,
    [data],
  );
  const preferences = useMemo(
    () => data?.preferences ?? DEFAULT_DATA.preferences,
    [data],
  );
  const videoProgress = useMemo(() => data?.videoProgress ?? {}, [data]);

  return {
    isLoaded,
    gamification,
    preferences,
    videoProgress,
    updateVideoProgress,
    getVideoProgress,
    getOverallProgress,
    addXP,
    getLevelProgress,
    xpLevels: XP_LEVELS,
    unlockAchievement,
    hasAchievement,
    updatePreference,
    resetAll,
  };
}

export type UseAgrelliflixStorageReturn = ReturnType<typeof useAgrelliflixStorage>;
