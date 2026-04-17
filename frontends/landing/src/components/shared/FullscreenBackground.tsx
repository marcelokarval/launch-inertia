/**
 * Full-viewport background image with dark overlay.
 *
 * Used by Onboarding, Checkout, and any page needing a fixed background.
 * Renders as a fixed-position layer behind all content.
 */

interface FullscreenBackgroundProps {
  /** Image URL (absolute or relative to /static/) */
  imageUrl: string;
  /** Background position (default: 'right center') */
  position?: string;
  /** Overlay opacity 0-1 (default: 0 = no overlay) */
  overlayOpacity?: number;
  /** Overlay color (default: black) */
  overlayColor?: string;
}

export default function FullscreenBackground({
  imageUrl,
  position = 'right center',
  overlayOpacity = 0,
  overlayColor = '#000000',
}: FullscreenBackgroundProps) {
  return (
    <>
      <div
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: `url(${imageUrl})`,
          backgroundSize: 'cover',
          backgroundPosition: position,
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'fixed',
          width: '100vw',
          height: '100vh',
        }}
        aria-hidden="true"
      />
      {overlayOpacity > 0 && (
        <div
          className="fixed inset-0 z-0"
          style={{ backgroundColor: overlayColor, opacity: overlayOpacity }}
          aria-hidden="true"
        />
      )}
    </>
  );
}
