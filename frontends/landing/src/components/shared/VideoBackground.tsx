/**
 * Full-viewport YouTube video background with overlay.
 *
 * Renders a fixed YouTube iframe behind content. The video autoplays muted
 * with loop enabled. An overlay div darkens the video for text legibility.
 *
 * Used by: SuporteLaunch page.
 */
interface VideoBackgroundProps {
  /** YouTube video ID */
  videoId: string;
  /** Overlay opacity (0 = no overlay, 1 = fully dark). Default: 0.52 */
  overlayOpacity?: number;
  /** Video zoom level (1 = normal, 1.2 = slight zoom). Default: 1.2 */
  zoom?: number;
}

export default function VideoBackground({
  videoId,
  overlayOpacity = 0.52,
  zoom = 1.2,
}: VideoBackgroundProps) {
  const src = `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&loop=1&playlist=${videoId}&controls=0&showinfo=0&rel=0&modestbranding=1&playsinline=1`;

  return (
    <div className="fixed inset-0 z-0 overflow-hidden">
      {/* YouTube iframe */}
      <iframe
        src={src}
        className="pointer-events-none absolute inset-0 h-full w-full border-0"
        style={{
          transform: zoom !== 1 ? `scale(${zoom})` : undefined,
          transformOrigin: 'center center',
        }}
        allow="autoplay; encrypted-media"
        loading="lazy"
        title="Background video"
        aria-hidden="true"
      />

      {/* Dark overlay */}
      <div
        className="absolute inset-0 bg-black"
        style={{ opacity: overlayOpacity }}
        aria-hidden="true"
      />
    </div>
  );
}
