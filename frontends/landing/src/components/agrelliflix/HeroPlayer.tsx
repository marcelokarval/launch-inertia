/**
 * HeroPlayer — main video player orchestrator.
 *
 * Manages player states (idle/loading/playing/ended), theater mode,
 * thumbnail overlay, YouTube embed, end-screen CTA, and playlist panel.
 *
 * Adapted from legacy hero-player-v2.tsx (721 lines → split into
 * HeroPlayer + PlaylistPanel + existing standalone components).
 *
 * Max 150 lines.
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Play, Maximize2, Minimize2, Calendar, Loader2 } from 'lucide-react';

import type { AgrelliflixEpisode, ProgressRecord, AgrelliflixThemeConfig } from '@/types';

import YouTubePlayer from './YouTubePlayer';
import EndScreenCTA from './EndScreenCTA';
import PlaylistPanel from './PlaylistPanel';
import XPLevelDisplay from './XPLevelDisplay';
import ViewerCountBadge from './ViewerCountBadge';
import {
  useViewerSimulation,
  useAgrelliflixStorage,
} from '@/hooks/agrelliflix';

type PlayerState = 'IDLE' | 'LOADING' | 'PLAYING' | 'ENDED';

interface HeroPlayerProps {
  episode: AgrelliflixEpisode;
  episodes: AgrelliflixEpisode[];
  unlockedEpisodes: number[];
  progress: ProgressRecord;
  initialViewers: number;
  ctaText: string;
  ctaUrl: string;
  theme: AgrelliflixThemeConfig;
  onEpisodeClick: (ep: AgrelliflixEpisode) => void;
  onProgressUpdate?: (currentTime: number, duration: number, pct: number) => void;
  onVideoComplete?: () => void;
}

export default function HeroPlayer({
  episode, episodes, unlockedEpisodes, progress,
  initialViewers, ctaText, ctaUrl, theme,
  onEpisodeClick, onProgressUpdate, onVideoComplete,
}: HeroPlayerProps) {
  const { currentViewers } = useViewerSimulation({ initialCount: initialViewers });
  const { updateVideoProgress, gamification, getLevelProgress, xpLevels } = useAgrelliflixStorage();
  const playerRef = useRef<HTMLDivElement>(null);

  const [state, setState] = useState<PlayerState>('IDLE');
  const [theater, setTheater] = useState(false);
  const [playlistOpen, setPlaylistOpen] = useState(true);
  const [playerKey, setPlayerKey] = useState(0);

  // Reset on episode change
  useEffect(() => { setState('IDLE'); setPlayerKey((k) => k + 1); }, [episode.id]);

  // Escape exits theater
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setTheater(false); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handlePlay = useCallback(() => {
    if (episode.is_live_pending && episode.youtube_url) {
      window.open(episode.youtube_url, '_blank', 'noopener,noreferrer');
      return;
    }
    setState('LOADING');
  }, [episode]);

  const handleProgress = useCallback((t: number, d: number, pct: number) => {
    if (state === 'LOADING' && t > 0) setState('PLAYING');
    updateVideoProgress(episode.id, t, d);
    onProgressUpdate?.(t, d, pct);
  }, [episode.id, state, updateVideoProgress, onProgressUpdate]);

  const handleComplete = useCallback(() => { setState('ENDED'); onVideoComplete?.(); }, [onVideoComplete]);

  const nextEp = (() => {
    const idx = episodes.findIndex((e) => e.id === episode.id);
    const next = episodes[idx + 1];
    return next && unlockedEpisodes.includes(next.id) ? next : null;
  })();

  const { percentage: xpPct } = getLevelProgress();
  const levelLabel = xpLevels[gamification.level]?.label ?? gamification.level;

  return (
    <div className="relative">
      {/* Background blur (normal mode only) */}
      {!theater && (
        <div className="absolute inset-0 overflow-hidden z-0">
          <img src={`https://img.youtube.com/vi/${episode.video_id}/maxresdefault.jpg`} alt="" className={`absolute inset-0 w-full h-full object-cover opacity-15 blur-2xl scale-110 ${episode.is_live_pending ? 'grayscale' : ''}`} />
          <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/70 to-black" />
        </div>
      )}

      <div className="relative z-10">
        {/* Top bar (hidden in theater) */}
        {!theater && (
          <div className="max-w-7xl mx-auto px-4 pt-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-xl md:text-2xl font-bold text-white">{episode.title}</h2>
              <XPLevelDisplay level={levelLabel} xp={gamification.xp} percentage={xpPct} xpToNextLevel={getLevelProgress().xpToNextLevel} goldAccent={theme.gold_accent} />
            </div>
            <ViewerCountBadge count={currentViewers} redPrimary={theme.red_primary} />
          </div>
        )}

        {/* Player + Playlist grid */}
        <div className={theater ? 'fixed inset-0 z-50 bg-black' : 'max-w-7xl mx-auto px-4 mt-6'}>
          <div className={theater ? 'w-full h-full' : 'grid grid-cols-1 lg:grid-cols-12 gap-6'}>
            {/* Video container */}
            <div ref={playerRef} className={theater ? 'w-full h-full' : 'lg:col-span-8'}>
              <div className={`relative w-full overflow-hidden bg-black ${theater ? 'h-full' : 'aspect-video rounded-xl border border-white/10'}`}>
                {/* Thumbnail */}
                <AnimatePresence>
                  {state === 'IDLE' && (
                    <motion.div initial={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-10">
                      <img src={`https://img.youtube.com/vi/${episode.video_id}/maxresdefault.jpg`} alt={episode.title} className={`w-full h-full object-cover ${episode.is_live_pending ? 'grayscale' : ''}`} />
                      <button type="button" onClick={handlePlay} className="absolute inset-0 flex flex-col items-center justify-center bg-black/40 gap-4 group">
                        <div className="w-20 h-20 rounded-full flex items-center justify-center shadow-2xl group-hover:scale-110 transition-transform" style={{ backgroundColor: episode.is_live_pending ? '#D97706' : theme.red_primary }}>
                          {episode.is_live_pending ? <Calendar className="w-10 h-10 text-white" /> : <Play className="w-10 h-10 text-white ml-1" />}
                        </div>
                        {episode.is_live_pending && <span className="text-amber-400 font-semibold text-lg">Clique para Agendar no YouTube</span>}
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
                {/* Loading */}
                <AnimatePresence>
                  {state === 'LOADING' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-20 flex items-center justify-center bg-black/70">
                      <Loader2 className="w-12 h-12 text-white animate-spin" style={{ color: theme.red_primary }} />
                    </motion.div>
                  )}
                </AnimatePresence>
                {/* YouTube */}
                {state !== 'IDLE' && (
                  <div className="absolute inset-0">
                    <YouTubePlayer key={`yt-${playerKey}`} videoId={episode.video_id} autoplay onProgressUpdate={handleProgress} onVideoComplete={handleComplete} onPlay={() => setState('PLAYING')} />
                  </div>
                )}
                {/* End screen */}
                <AnimatePresence>
                  {state === 'ENDED' && <EndScreenCTA text={ctaText} url={ctaUrl} nextEpisode={nextEp} onNextEpisode={nextEp ? () => onEpisodeClick(nextEp) : undefined} redPrimary={theme.red_primary} />}
                </AnimatePresence>
                {/* Theater toggle */}
                <button type="button" onClick={() => setTheater((t) => !t)} className="absolute top-4 right-4 z-20 p-2 rounded-lg text-white transition-colors hover:opacity-80" style={{ backgroundColor: theme.red_primary }}>
                  {theater ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                </button>
              </div>
            </div>
            {/* Playlist (normal mode only) */}
            {!theater && (
              <div className="lg:col-span-4">
                <PlaylistPanel episodes={episodes} currentEpisodeId={episode.id} unlockedEpisodes={unlockedEpisodes} progress={progress} onEpisodeClick={onEpisodeClick} isExpanded={playlistOpen} onToggle={() => setPlaylistOpen((o) => !o)} redPrimary={theme.red_primary} />
              </div>
            )}
          </div>

          {/* Episode info (below player, normal mode) */}
          {!theater && (
            <div className="mt-6 pb-8 lg:max-w-[66%] space-y-3">
              <h1 className="text-xl md:text-2xl font-bold text-white">{episode.subtitle}</h1>
              <p className="text-base text-white/60 leading-relaxed">{episode.description}</p>
              <div className="flex flex-wrap items-center gap-4 text-sm text-white/40">
                <span>{episode.duration}</span>
                <span>{currentViewers.toLocaleString()} assistindo agora</span>
              </div>
              {episode.chapters.length > 0 && (
                <div className="pt-4 mt-4 border-t border-white/10">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-medium text-white/40 mr-1">Capitulos</span>
                    {episode.chapters.map((ch, i, arr) => {
                      const t = i / (arr.length - 1 || 1);
                      return (
                        <span key={i} className="inline-flex items-center px-2.5 py-1 text-xs rounded-md" style={{ backgroundColor: `rgba(229,9,20,${0.08 + t * 0.1})`, border: `1px solid rgba(229,9,20,${0.15 + t * 0.2})`, color: `rgba(255,255,255,${0.55 + t * 0.35})` }}>
                          {ch.title}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
