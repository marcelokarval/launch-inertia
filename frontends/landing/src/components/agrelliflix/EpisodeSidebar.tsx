/**
 * Episode sidebar — desktop vertical list + mobile horizontal carousel.
 */
import type { AgrelliflixEpisode, ProgressRecord } from '@/types';

import EpisodeCard from './EpisodeCard';

interface EpisodeSidebarProps {
  episodes: AgrelliflixEpisode[];
  currentEpisodeId: number;
  unlockedEpisodes: number[];
  progress: ProgressRecord;
  onEpisodeClick: (episode: AgrelliflixEpisode) => void;
  isMobile: boolean;
  redPrimary: string;
  goldAccent: string;
}

export default function EpisodeSidebar({
  episodes,
  currentEpisodeId,
  unlockedEpisodes,
  progress,
  onEpisodeClick,
  isMobile,
  redPrimary,
  goldAccent,
}: EpisodeSidebarProps) {
  if (isMobile) {
    return (
      <div className="flex gap-3 overflow-x-auto pb-2 px-4 scrollbar-hide">
        {episodes.map((ep) => (
          <div key={ep.id} className="flex-shrink-0 w-48">
            <EpisodeCard
              episode={ep}
              progress={progress[ep.id]}
              isLocked={!unlockedEpisodes.includes(ep.id)}
              isActive={ep.id === currentEpisodeId}
              onClick={() => onEpisodeClick(ep)}
              redPrimary={redPrimary}
              goldAccent={goldAccent}
            />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 w-80 overflow-y-auto max-h-[calc(100vh-200px)]">
      <h3 className="text-white/60 text-xs uppercase tracking-wider px-2 mb-1">
        Episodios
      </h3>
      {episodes.map((ep) => (
        <EpisodeCard
          key={ep.id}
          episode={ep}
          progress={progress[ep.id]}
          isLocked={!unlockedEpisodes.includes(ep.id)}
          isActive={ep.id === currentEpisodeId}
          onClick={() => onEpisodeClick(ep)}
          redPrimary={redPrimary}
          goldAccent={goldAccent}
        />
      ))}
    </div>
  );
}
