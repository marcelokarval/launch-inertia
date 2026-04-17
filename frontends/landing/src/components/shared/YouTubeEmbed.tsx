/**
 * Simple YouTube iframe embed with mute/unmute overlay.
 *
 * Lighter alternative to the AgreliFlix YouTubePlayer (react-youtube).
 * Used for pages that just need a video embed without progress tracking.
 *
 * Features:
 * - Autoplay muted (browser policy)
 * - Pulsing unmute button overlay
 * - 16:9 aspect ratio via aspect-video
 */
import { useCallback, useMemo, useRef, useState } from 'react';

import { IconVolume } from '@/components/shared/icons';

/**
 * Validate YouTube video ID format.
 *
 * YouTube video IDs are 11 characters: alphanumeric plus `-` and `_`.
 * This prevents URL injection if a malformed ID is passed from config.
 */
const YOUTUBE_ID_REGEX = /^[a-zA-Z0-9_-]{11}$/;

function validateYouTubeId(videoId: string): string {
  if (YOUTUBE_ID_REGEX.test(videoId)) {
    return videoId;
  }
  // Return empty string for invalid IDs — iframe will show YouTube error
  console.warn(`[YouTubeEmbed] Invalid video ID: ${videoId}`);
  return '';
}

interface YouTubeEmbedProps {
  /** YouTube video ID */
  videoId: string;
  /** Video title for accessibility */
  title?: string;
  /** Auto-play on mount (muted required by browsers) */
  autoplay?: boolean;
  /** Additional className for container */
  className?: string;
}

export default function YouTubeEmbed({
  videoId,
  title = 'Video',
  autoplay = true,
  className = '',
}: YouTubeEmbedProps) {
  const [isMuted, setIsMuted] = useState(autoplay);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Validate video ID once to prevent URL injection
  const safeVideoId = useMemo(() => validateYouTubeId(videoId), [videoId]);

  const handleUnmute = useCallback(() => {
    if (iframeRef.current && safeVideoId) {
      const muteParam = isMuted ? '0' : '1';
      iframeRef.current.src =
        `https://www.youtube.com/embed/${safeVideoId}?autoplay=1&mute=${muteParam}&rel=0&modestbranding=1`;
      setIsMuted(false);
    }
  }, [safeVideoId, isMuted]);

  const src = safeVideoId
    ? `https://www.youtube.com/embed/${safeVideoId}?autoplay=${autoplay ? 1 : 0}&mute=${isMuted ? 1 : 0}&rel=0&modestbranding=1`
    : '';

  return (
    <div className={`relative aspect-video w-full ${className}`}>
      <iframe
        ref={iframeRef}
        className="absolute inset-0 h-full w-full rounded-lg"
        src={src}
        title={title}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />

      {/* Unmute overlay */}
      {isMuted && (
        <div className="absolute inset-0 z-20 flex items-center justify-center">
          {/* Pulse ring */}
          <div
            className="absolute h-20 w-20 animate-ping rounded-full opacity-30 md:h-24 md:w-24"
            style={{ backgroundColor: '#FF0000' }}
          />

          <button
            onClick={handleUnmute}
            className="relative rounded-full border-2 bg-black/90 p-6 text-white transition-all duration-300 hover:scale-110 hover:bg-black md:p-8"
            style={{
              borderColor: 'rgba(255, 107, 107, 0.9)',
              boxShadow:
                '0 0 30px rgba(255, 107, 107, 0.4), 0 0 60px rgba(255, 107, 107, 0.3)',
            }}
            aria-label="Ativar áudio"
          >
            <IconVolume className="h-8 w-8 md:h-12 md:w-12" style={{ color: 'rgba(255, 107, 107, 0.9)' }} />
            <span className="absolute -bottom-12 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-black/80 px-4 py-2 text-sm font-medium text-white md:text-base">
              Clique para ativar o áudio
            </span>
          </button>
        </div>
      )}
    </div>
  );
}
