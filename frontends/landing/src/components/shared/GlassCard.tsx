/**
 * Glassmorphism card component.
 *
 * Semi-transparent card with backdrop blur, used throughout landing pages.
 * Accepts border color override for accent theming.
 */
import type { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  /** Border accent color (CSS value). Default: gray-700 */
  borderColor?: string;
  /** Additional className */
  className?: string;
}

export default function GlassCard({
  children,
  borderColor,
  className = '',
}: GlassCardProps) {
  return (
    <div
      className={`rounded-xl border border-gray-700 bg-gray-800/50 p-6 backdrop-blur-sm ${className}`}
      style={borderColor ? { borderColor } : undefined}
    >
      {children}
    </div>
  );
}
