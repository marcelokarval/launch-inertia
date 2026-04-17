/**
 * Countdown timer to a specific target date.
 *
 * Different from thank-you/CountdownTimer (minutes-based).
 * This one counts down to an ISO 8601 date, showing days/hours/minutes/seconds.
 *
 * Used by: LembreteBF, promotional pages with deadlines.
 */
import { useEffect, useState } from 'react';

interface DateCountdownProps {
  /** ISO 8601 target date string */
  targetDate: string;
  /** Callback when countdown reaches zero */
  onExpire?: () => void;
  /** Background color for the countdown bar */
  bgColor?: string;
  /** Text color */
  textColor?: string;
  /** Additional className */
  className?: string;
  /** Show as fixed top bar */
  fixed?: boolean;
}

interface TimeLeft {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

function calculateTimeLeft(targetDate: string): TimeLeft | null {
  const diff = new Date(targetDate).getTime() - Date.now();
  if (diff <= 0) return null;

  return {
    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
    hours: Math.floor((diff / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((diff / (1000 * 60)) % 60),
    seconds: Math.floor((diff / 1000) % 60),
  };
}

export default function DateCountdown({
  targetDate,
  onExpire,
  bgColor = '#FF1F5A',
  textColor = '#ffffff',
  className = '',
  fixed = false,
}: DateCountdownProps) {
  const [timeLeft, setTimeLeft] = useState<TimeLeft | null>(() =>
    calculateTimeLeft(targetDate),
  );

  useEffect(() => {
    const interval = setInterval(() => {
      const tl = calculateTimeLeft(targetDate);
      setTimeLeft(tl);
      if (!tl) {
        clearInterval(interval);
        onExpire?.();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [targetDate, onExpire]);

  if (!timeLeft) {
    return (
      <div
        className={`py-3 text-center font-bold ${fixed ? 'fixed top-0 left-0 right-0 z-50' : ''} ${className}`}
        style={{ backgroundColor: bgColor, color: textColor }}
      >
        OFERTA ENCERRADA
      </div>
    );
  }

  const pad = (n: number) => String(n).padStart(2, '0');

  return (
    <div
      className={`flex items-center justify-center gap-2 py-3 text-center font-bold md:gap-4 ${fixed ? 'fixed top-0 left-0 right-0 z-50' : ''} ${className}`}
      style={{ backgroundColor: bgColor, color: textColor }}
    >
      <span className="text-sm md:text-base">OFERTA ENCERRA EM:</span>
      <div className="flex items-center gap-1 font-mono text-lg md:text-xl">
        {timeLeft.days > 0 && (
          <>
            <span>{pad(timeLeft.days)}d</span>
            <span className="opacity-60">:</span>
          </>
        )}
        <span>{pad(timeLeft.hours)}h</span>
        <span className="opacity-60">:</span>
        <span>{pad(timeLeft.minutes)}m</span>
        <span className="opacity-60">:</span>
        <span>{pad(timeLeft.seconds)}s</span>
      </div>
    </div>
  );
}
