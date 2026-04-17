/**
 * Sales page header — black bar with logo and live countdown.
 *
 * Fixed position, shows "ABERTURA EM:" countdown to target date,
 * or "INSCRIÇÕES ABERTAS" after expiry.
 */
import { useEffect, useState } from 'react';

interface SalesHeaderProps {
  /** Target date for countdown (ISO 8601) */
  targetDate?: string;
  /** Logo image URL (optional) */
  logoUrl?: string;
}

interface TimeLeft {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

function calcTimeLeft(target: string): TimeLeft | null {
  const diff = new Date(target).getTime() - Date.now();
  if (diff <= 0) return null;
  return {
    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
    hours: Math.floor((diff / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((diff / (1000 * 60)) % 60),
    seconds: Math.floor((diff / 1000) % 60),
  };
}

function CountdownUnit({ value, label }: { value: number; label: string }) {
  return (
    <div className="text-center">
      <div className="min-w-[40px] rounded bg-red-600 px-2 py-1 font-mono text-lg font-bold text-white md:min-w-[50px] md:text-2xl">
        {String(value).padStart(2, '0')}
      </div>
      <span className="mt-0.5 block text-[10px] uppercase text-white/60 md:text-xs">
        {label}
      </span>
    </div>
  );
}

export default function SalesHeader({ targetDate, logoUrl }: SalesHeaderProps) {
  const [timeLeft, setTimeLeft] = useState<TimeLeft | null>(() =>
    targetDate ? calcTimeLeft(targetDate) : null,
  );

  useEffect(() => {
    if (!targetDate) return;
    const interval = setInterval(() => {
      const tl = calcTimeLeft(targetDate);
      setTimeLeft(tl);
      if (!tl) clearInterval(interval);
    }, 1000);
    return () => clearInterval(interval);
  }, [targetDate]);

  return (
    <header className="fixed left-0 right-0 top-0 z-50 bg-black shadow-lg">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-2 md:py-3">
        {/* Logo */}
        {logoUrl && (
          <img
            src={logoUrl}
            alt="Logo"
            className="h-8 w-auto md:h-10"
            loading="eager"
          />
        )}

        {/* Countdown or "OPEN" badge */}
        {timeLeft ? (
          <div className="flex items-center gap-2 md:gap-3">
            <span className="text-xs font-bold uppercase tracking-wide text-white/80 md:text-sm">
              Abertura em:
            </span>
            <div className="flex gap-1 md:gap-2">
              <CountdownUnit value={timeLeft.days} label="Dias" />
              <CountdownUnit value={timeLeft.hours} label="Hrs" />
              <CountdownUnit value={timeLeft.minutes} label="Min" />
              <CountdownUnit value={timeLeft.seconds} label="Seg" />
            </div>
          </div>
        ) : (
          <div className="rounded-full bg-green-500 px-4 py-1 text-sm font-bold text-white md:text-base">
            INSCRIÇÕES ABERTAS
          </div>
        )}
      </div>
    </header>
  );
}
