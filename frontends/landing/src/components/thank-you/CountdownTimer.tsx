import { useEffect, useState } from 'react';

interface CountdownTimerProps {
  /** Total countdown duration in minutes */
  initialMinutes?: number;
  /** Callback when timer expires */
  onExpire?: () => void;
  /** Optional label above the timer */
  label?: string;
}

/**
 * Countdown timer with urgency mode.
 *
 * Shows MM:SS format. Turns red in the last 60 seconds.
 * Calls onExpire when timer reaches zero.
 */
export default function CountdownTimer({
  initialMinutes = 15,
  onExpire,
  label,
}: CountdownTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState(initialMinutes * 60);

  useEffect(() => {
    if (secondsLeft <= 0) {
      onExpire?.();
      return;
    }

    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onExpire?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [secondsLeft, onExpire]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const isUrgent = secondsLeft <= 60 && secondsLeft > 0;
  const isExpired = secondsLeft <= 0;

  if (isExpired) {
    return (
      <div className="text-center">
        <p className="text-sm font-medium text-red-600">
          Tempo esgotado! As vagas podem ter sido preenchidas.
        </p>
      </div>
    );
  }

  return (
    <div className="text-center">
      {label && (
        <p className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">
          {label}
        </p>
      )}
      <div
        className={`inline-flex items-baseline gap-1 rounded-lg px-4 py-2 font-mono text-2xl font-bold tabular-nums transition-colors ${
          isUrgent
            ? 'animate-pulse bg-red-50 text-red-600'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        <span>{String(minutes).padStart(2, '0')}</span>
        <span className={isUrgent ? 'animate-pulse' : ''}>:</span>
        <span>{String(seconds).padStart(2, '0')}</span>
      </div>
    </div>
  );
}
