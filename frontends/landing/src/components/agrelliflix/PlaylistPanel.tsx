/**
 * Expandable playlist panel — shows all episodes with thumbnails,
 * progress bars, and lock/scheduled states.
 *
 * Extracted from legacy hero-player-v2.tsx PlaylistPanel section.
 * Max 150 lines.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Play, Clock, Calendar, Lock } from 'lucide-react';

import type { AgrelliflixEpisode, ProgressRecord } from '@/types';

interface PlaylistPanelProps {
  episodes: AgrelliflixEpisode[];
  currentEpisodeId: number;
  unlockedEpisodes: number[];
  progress: ProgressRecord;
  onEpisodeClick: (episode: AgrelliflixEpisode) => void;
  isExpanded: boolean;
  onToggle: () => void;
  redPrimary: string;
}

export default function PlaylistPanel({
  episodes,
  currentEpisodeId,
  unlockedEpisodes,
  progress,
  onEpisodeClick,
  isExpanded,
  onToggle,
  redPrimary,
}: PlaylistPanelProps) {
  return (
    <div className="rounded-xl border border-white/10 overflow-hidden bg-white/5">
      {/* Header — always visible */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-white font-semibold">Aulas do Treinamento</span>
          <span className="text-xs text-white/40 bg-white/10 px-2 py-1 rounded-full">
            {episodes.length} aulas
          </span>
        </div>
        <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-5 h-5 text-white/40" />
        </motion.div>
      </button>

      {/* Expandable episode list */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="p-4 pt-0 space-y-2">
              {episodes.map((ep, index) => {
                const isUnlocked = unlockedEpisodes.includes(ep.id);
                const isCurrent = ep.id === currentEpisodeId;
                const pct = progress[ep.id]?.percentage ?? 0;
                const isPending = ep.is_live_pending;

                return (
                  <button
                    key={ep.id}
                    type="button"
                    onClick={() => (isPending || isUnlocked) && onEpisodeClick(ep)}
                    disabled={!isUnlocked && !isPending}
                    className={`w-full flex gap-4 p-3 rounded-lg transition-all text-left ${
                      isCurrent
                        ? 'border bg-white/5'
                        : isPending
                          ? 'bg-amber-900/20 border border-amber-600/30 hover:border-amber-500/50'
                          : isUnlocked
                            ? 'bg-white/5 hover:bg-white/10 border border-transparent'
                            : 'bg-white/[0.02] opacity-50 cursor-not-allowed border border-transparent'
                    }`}
                    style={isCurrent ? { borderColor: redPrimary, backgroundColor: `${redPrimary}20` } : {}}
                  >
                    {/* Thumbnail */}
                    <div className="relative w-28 aspect-video rounded-lg overflow-hidden flex-shrink-0">
                      <img
                        src={`https://img.youtube.com/vi/${ep.video_id}/mqdefault.jpg`}
                        alt={ep.title}
                        className={`w-full h-full object-cover ${isPending ? 'grayscale' : ''}`}
                      />
                      {pct > 0 && !isPending && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
                          <div className="h-full" style={{ width: `${pct}%`, backgroundColor: redPrimary }} />
                        </div>
                      )}
                      <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                        {isPending ? (
                          <Calendar className="w-6 h-6 text-amber-400" />
                        ) : !isUnlocked ? (
                          <Lock className="w-5 h-5 text-white/50" />
                        ) : (
                          <Play className={`w-6 h-6 ${isCurrent ? 'text-white' : 'text-white/80'}`} />
                        )}
                      </div>
                      <span
                        className={`absolute top-1 left-1 text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          isPending ? 'bg-amber-600/90 text-white' : 'bg-black/70 text-white'
                        }`}
                      >
                        {isPending ? 'LIVE' : index + 1}
                      </span>
                    </div>

                    {/* Info */}
                    <div className="flex-1">
                      <h4
                        className={`font-medium text-sm ${
                          isCurrent ? '' : isPending ? 'text-amber-400' : 'text-white'
                        }`}
                        style={isCurrent ? { color: redPrimary } : {}}
                      >
                        {ep.title}
                      </h4>
                      <p className="text-xs text-white/40 line-clamp-1 mt-0.5">{ep.subtitle}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        {isPending ? (
                          <span className="text-xs text-amber-500 flex items-center gap-1 font-medium">
                            <Calendar className="w-3 h-3" />
                            Agendar Live
                          </span>
                        ) : (
                          <>
                            <span className="text-xs text-white/40 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {ep.duration}
                            </span>
                            {pct > 0 && (
                              <span className="text-xs text-white/40">
                                • {Math.round(pct)}% assistido
                              </span>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
