/**
 * Section heading with optional accent underline.
 *
 * Used across sales pages, promotional pages for consistent heading style.
 */
import type { ReactNode } from 'react';

interface SectionHeadingProps {
  children: ReactNode;
  /** Optional subtitle below the heading */
  subtitle?: string;
  /** Text alignment */
  align?: 'left' | 'center' | 'right';
  /** Show accent underline */
  underline?: boolean;
  /** Underline color (CSS value) */
  underlineColor?: string;
  /** Additional className */
  className?: string;
}

export default function SectionHeading({
  children,
  subtitle,
  align = 'center',
  underline = false,
  underlineColor = 'var(--color-brand-primary)',
  className = '',
}: SectionHeadingProps) {
  const alignClass = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }[align];

  return (
    <div className={`mb-8 ${alignClass} ${className}`}>
      <h2 className="text-2xl font-bold text-white md:text-3xl lg:text-4xl">
        {children}
      </h2>
      {underline && (
        <div
          className="mx-auto mt-3 h-1 w-20 rounded-full"
          style={{
            backgroundColor: underlineColor,
            marginLeft: align === 'left' ? '0' : undefined,
            marginRight: align === 'right' ? '0' : undefined,
          }}
        />
      )}
      {subtitle && (
        <p className="mt-3 text-base text-gray-400 md:text-lg">{subtitle}</p>
      )}
    </div>
  );
}
