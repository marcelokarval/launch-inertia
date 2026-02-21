/**
 * Episode card for the sidebar/grid.
 *
 * Shows episode thumbnail, title, progress bar, lock state, and countdown.
 */
import { Lock, Play, CheckCircle } from 'lucide-react';

import type { AgrelliflixEpisode, VideoProgress } from '@/types';

import CountdownTimer from './CountdownTimer';

interface EpisodeCardProps {
  episode: AgrelliflixEpisode;
  progress?: VideoProgress | null;
  isLocked: boolean;
  isActive: boolean;
  onClick: () => void;
  redPrimary: string;
  goldAccent: string;
}

export default function EpisodeCard({
  episode,
  progress,
  isLocked,
  isActive,
  onClick,
  redPrimary,
  goldAccent,
}: EpisodeCardProps) {
  const percentage = progress?.percentage ?? 0;
  const isCompleted = progress?.completed ?? false;

  return (
    <button
      type="button"
      onClick={() => !isLocked && onClick()}
      disabled={isLocked}
      className={`
        w-full text-left rounded-lg overflow-hidden transition-all duration-200
        ${isActive ? 'ring-2' : 'hover:bg-white/5'}
        ${isLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      style={isActive ? { outlineColor: redPrimary, outline: `2px solid ${redPrimary}`, backgroundColor: 'rgba(255,255,255,0.05)' } : {}}
    >
      {/* Thumbnail area */}
      <div className="relative aspect-video bg-black/30 flex items-center justify-center">
        <img
          src={`https://img.youtube.com/vi/${episode.video_id}/mqdefault.jpg`}
          alt={episode.title}
          className="w-full h-full object-cover"
          loading="lazy"
        />
        {/* Overlay */}
        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
          {isLocked ? (
            <Lock size={24} className="text-white/60" />
          ) : isCompleted ? (
            <CheckCircle size={24} style={{ color: goldAccent }} />
          ) : (
            <Play size={24} className="text-white" />
          )}
        </div>
        {/* Progress bar */}
        {percentage > 0 && !isLocked && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
            <div
              className="h-full transition-all"
              style={{
                width: `${percentage}%`,
                backgroundColor: isCompleted ? goldAccent : redPrimary,
              }}
            />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h4 className="text-white font-medium text-sm">{episode.title}</h4>
        <p className="text-white/50 text-xs mt-0.5 line-clamp-1">{episode.subtitle}</p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-white/40 text-xs">{episode.duration}</span>
          {isLocked && episode.is_live_pending && (
            <CountdownTimer targetDate={episode.available_at} className="text-xs" />
          )}
        </div>
      </div>
    </button>
  );
}
