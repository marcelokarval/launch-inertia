/**
 * YouTube player wrapper using react-youtube.
 *
 * Provides a clean interface for the AgreliFlix video player with
 * progress tracking callbacks. Handles ready, play, pause, end events.
 *
 * Max 150 lines — complex controls are in HeroPlayer parent.
 */
import { useCallback, useRef } from 'react';
import YouTube from 'react-youtube';
import type { YouTubeEvent, YouTubePlayer as YTPlayer } from 'react-youtube';

interface YouTubePlayerProps {
  videoId: string;
  /** Called periodically with (currentTime, duration, percentage) */
  onProgressUpdate?: (currentTime: number, duration: number, pct: number) => void;
  onVideoComplete?: () => void;
  onReady?: () => void;
  onPlay?: () => void;
  onPause?: () => void;
  onBuffering?: () => void;
  autoplay?: boolean;
  className?: string;
}

export default function YouTubePlayer({
  videoId,
  onProgressUpdate,
  onVideoComplete,
  onReady,
  onPlay,
  onPause,
  onBuffering,
  autoplay = false,
  className = '',
}: YouTubePlayerProps) {
  const playerRef = useRef<YTPlayer | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startTracking = useCallback(() => {
    if (intervalRef.current) return;
    intervalRef.current = setInterval(() => {
      const player = playerRef.current;
      if (!player) return;
      try {
        const current = player.getCurrentTime();
        const duration = player.getDuration();
        if (duration > 0) {
          const pct = (current / duration) * 100;
          onProgressUpdate?.(current, duration, pct);
          if (pct >= 98) {
            onVideoComplete?.();
          }
        }
      } catch {
        // Player may be destroyed
      }
    }, 3000);
  }, [onProgressUpdate, onVideoComplete]);

  const stopTracking = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const handleReady = useCallback(
    (e: YouTubeEvent) => {
      playerRef.current = e.target;
      onReady?.();
    },
    [onReady],
  );

  const handleStateChange = useCallback(
    (e: YouTubeEvent) => {
      const state = e.data;
      // YT.PlayerState: -1=unstarted, 0=ended, 1=playing, 2=paused, 3=buffering
      if (state === 1) {
        startTracking();
        onPlay?.();
      } else if (state === 2) {
        stopTracking();
        onPause?.();
      } else if (state === 0) {
        stopTracking();
        onVideoComplete?.();
      } else if (state === 3) {
        onBuffering?.();
      }
    },
    [startTracking, stopTracking, onPlay, onPause, onVideoComplete, onBuffering],
  );

  const handleEnd = useCallback(() => {
    stopTracking();
    onVideoComplete?.();
  }, [stopTracking, onVideoComplete]);

  return (
    <div className={`relative w-full aspect-video ${className}`}>
      <YouTube
        videoId={videoId}
        opts={{
          width: '100%',
          height: '100%',
          playerVars: {
            autoplay: autoplay ? 1 : 0,
            modestbranding: 1,
            rel: 0,
            showinfo: 0,
            controls: 1,
            fs: 1,
            iv_load_policy: 3,
          },
        }}
        onReady={handleReady}
        onStateChange={handleStateChange}
        onEnd={handleEnd}
        className="w-full h-full"
        iframeClassName="w-full h-full rounded-lg"
      />
    </div>
  );
}
