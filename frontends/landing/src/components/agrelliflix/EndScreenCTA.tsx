/**
 * End-screen CTA overlay shown when video completes.
 *
 * Displays a call-to-action button with the configured text/URL.
 */
import { motion } from 'framer-motion';
import { ExternalLink } from 'lucide-react';

import type { AgrelliflixEpisode } from '@/types';

interface EndScreenCTAProps {
  text: string;
  url: string;
  nextEpisode?: AgrelliflixEpisode | null;
  onNextEpisode?: () => void;
  redPrimary: string;
}

export default function EndScreenCTA({
  text,
  url,
  nextEpisode,
  onNextEpisode,
  redPrimary,
}: EndScreenCTAProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-20 gap-4"
    >
      {nextEpisode && (
        <button
          type="button"
          onClick={onNextEpisode}
          className="px-6 py-3 rounded-lg text-white font-semibold text-lg transition-transform hover:scale-105"
          style={{ backgroundColor: redPrimary }}
        >
          Proxima Aula: {nextEpisode.title} →
        </button>
      )}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 px-6 py-3 rounded-lg text-white font-semibold transition-transform hover:scale-105 border border-white/20 bg-white/10 backdrop-blur"
      >
        <ExternalLink size={18} />
        {text}
      </a>
    </motion.div>
  );
}
