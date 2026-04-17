/**
 * Floating CTA button — sticky bottom bar that appears after scrolling.
 *
 * Shows a green WhatsApp-style CTA button fixed to the bottom of the viewport.
 * Only visible after the user scrolls past a threshold.
 */
import { useEffect, useState } from 'react';

interface FloatingCTAProps {
  /** CTA link */
  href: string;
  /** CTA button text */
  text: string;
  /** Scroll threshold in pixels before showing. Default: 400 */
  scrollThreshold?: number;
}

export default function FloatingCTA({
  href,
  text,
  scrollThreshold = 400,
}: FloatingCTAProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > scrollThreshold);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [scrollThreshold]);

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-40 transform bg-gradient-to-t from-black/80 to-transparent p-4 transition-transform duration-300 ${
        visible ? 'translate-y-0' : 'translate-y-full'
      }`}
    >
      <div className="mx-auto max-w-md">
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full rounded-xl bg-green-500 px-8 py-4 text-center text-lg font-bold text-white shadow-lg transition-all duration-300 hover:bg-green-600 hover:shadow-xl"
        >
          {text}
        </a>
      </div>
    </div>
  );
}
