/**
 * Single achievement badge with unlock animation.
 */
import { motion } from 'framer-motion';

import type { AgrelliflixAchievement } from '@/types';

interface AchievementBadgeProps {
  achievement: AgrelliflixAchievement;
  isUnlocked: boolean;
  goldAccent: string;
}

export default function AchievementBadge({
  achievement,
  isUnlocked,
  goldAccent,
}: AchievementBadgeProps) {
  return (
    <motion.div
      initial={isUnlocked ? { scale: 0.8, opacity: 0 } : false}
      animate={isUnlocked ? { scale: 1, opacity: 1 } : {}}
      className={`
        flex flex-col items-center gap-1 p-3 rounded-lg text-center
        ${isUnlocked ? '' : 'opacity-30 grayscale'}
      `}
      style={isUnlocked ? { backgroundColor: 'rgba(255, 215, 0, 0.1)', border: `1px solid ${goldAccent}` } : { backgroundColor: 'rgba(255,255,255,0.05)' }}
    >
      <span className="text-2xl">{achievement.icon || '🏆'}</span>
      <p className="text-white text-xs font-medium">{achievement.title}</p>
      <p className="text-white/40 text-[10px]">{achievement.points} XP</p>
    </motion.div>
  );
}
