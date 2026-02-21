/**
 * Mini-player — sticky top bar on mobile when scrolling past the video.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { Play, X } from 'lucide-react';

import type { AgrelliflixEpisode } from '@/types';

interface MiniPlayerProps {
  episode: AgrelliflixEpisode;
  isVisible: boolean;
  onClose: () => void;
  onResume: () => void;
  redPrimary: string;
}

export default function MiniPlayer({
  episode,
  isVisible,
  onClose,
  onResume,
  redPrimary,
}: MiniPlayerProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: -60, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -60, opacity: 0 }}
          className="fixed top-0 left-0 right-0 z-50 flex items-center gap-3 px-4 py-2"
          style={{ backgroundColor: '#0A0A0A', borderBottom: `2px solid ${redPrimary}` }}
        >
          <img
            src={`https://img.youtube.com/vi/${episode.video_id}/default.jpg`}
            alt={episode.title}
            className="w-10 h-7 rounded object-cover"
          />
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">{episode.title}</p>
            <p className="text-white/50 text-xs truncate">{episode.subtitle}</p>
          </div>
          <button
            type="button"
            onClick={onResume}
            className="p-2 rounded-full text-white"
            style={{ backgroundColor: redPrimary }}
          >
            <Play size={14} />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-white/40 hover:text-white"
          >
            <X size={16} />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
