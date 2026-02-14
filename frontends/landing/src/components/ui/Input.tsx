import { type InputHTMLAttributes, useId } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

/**
 * Landing page Input component.
 * Own styled component (NOT HeroUI — landing has its own design system).
 */
export default function Input({
  label,
  error,
  className = '',
  id: externalId,
  ...props
}: InputProps) {
  const autoId = useId();
  const inputId = externalId || autoId;

  return (
    <div className="w-full">
      <label
        htmlFor={inputId}
        className="mb-1.5 block text-sm font-medium text-[var(--color-text-primary)]"
      >
        {label}
      </label>
      <input
        id={inputId}
        className={`w-full rounded-lg border bg-[var(--color-surface-alt)] px-4 py-3 text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] ${
          error
            ? 'border-[var(--color-error)] focus:ring-[var(--color-error)]'
            : 'border-[var(--color-border)]'
        } ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-[var(--color-error)]">{error}</p>
      )}
    </div>
  );
}
