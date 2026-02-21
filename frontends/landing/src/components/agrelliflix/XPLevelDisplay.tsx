/**
 * XP level progress display for gamification.
 *
 * Shows current level name, XP bar, and points to next level.
 */
interface XPLevelDisplayProps {
  level: string;
  xp: number;
  percentage: number;
  xpToNextLevel: number;
  goldAccent: string;
}

export default function XPLevelDisplay({
  level,
  xp,
  percentage,
  xpToNextLevel,
  goldAccent,
}: XPLevelDisplayProps) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5">
      <div className="flex items-center gap-2">
        <span className="text-lg">⭐</span>
        <div>
          <p className="text-xs text-white/60 uppercase tracking-wider">
            {level}
          </p>
          <p className="text-xs" style={{ color: goldAccent }}>
            {xp} XP
          </p>
        </div>
      </div>
      <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(percentage, 100)}%`, backgroundColor: goldAccent }}
        />
      </div>
      {xpToNextLevel > 0 && (
        <span className="text-xs text-white/40 whitespace-nowrap">
          {xpToNextLevel} XP left
        </span>
      )}
    </div>
  );
}
