/**
 * Fixed countdown banner for Black Friday pages.
 *
 * Shows a prominent fixed-position bar at the top of the page with
 * a headline and individual countdown digit boxes (DIAS/HORAS/MIN/SEG).
 *
 * Uses the same countdown logic as shared/DateCountdown but with a
 * different visual treatment (individual boxes instead of inline text).
 */
import { useEffect, useState } from 'react';

interface CountdownBannerProps {
  /** ISO 8601 target date */
  targetDate: string;
  /** Headline text next to countdown */
  headline?: string;
  /** Background color */
  bgColor?: string;
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

function DigitBox({ value, label }: { value: number; label: string }) {
  return (
    <div className="text-center">
      <div className="min-w-[45px] rounded bg-white px-2 py-1 text-lg font-bold text-black md:min-w-[70px] md:px-4 md:py-3 md:text-3xl">
        {String(value).padStart(2, '0')}
      </div>
      <p className="mt-1 text-xs font-bold text-white md:text-base">{label}</p>
    </div>
  );
}

export default function CountdownBanner({
  targetDate,
  headline = 'A Black Friday Infinita termina em:',
  bgColor = '#FF1F5A',
}: CountdownBannerProps) {
  const [timeLeft, setTimeLeft] = useState<TimeLeft | null>(() =>
    calcTimeLeft(targetDate),
  );

  useEffect(() => {
    const interval = setInterval(() => {
      const tl = calcTimeLeft(targetDate);
      setTimeLeft(tl);
      if (!tl) clearInterval(interval);
    }, 1000);
    return () => clearInterval(interval);
  }, [targetDate]);

  if (!timeLeft) {
    return (
      <div
        className="fixed left-0 right-0 top-0 z-50 py-3 text-center font-bold text-white md:py-4"
        style={{ backgroundColor: bgColor }}
      >
        OFERTA ENCERRADA
      </div>
    );
  }

  return (
    <div
      className="fixed left-0 right-0 top-0 z-50"
      style={{ backgroundColor: bgColor }}
    >
      <div className="px-4 py-3 md:py-4">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-center gap-3 md:flex-row md:gap-6">
          <h2 className="text-center text-base font-bold uppercase leading-tight text-white md:text-left md:text-2xl lg:text-3xl">
            {headline}
          </h2>
          <div className="flex justify-center gap-2 md:gap-4">
            <DigitBox value={timeLeft.days} label="DIAS" />
            <DigitBox value={timeLeft.hours} label="HORAS" />
            <DigitBox value={timeLeft.minutes} label="MIN" />
            <DigitBox value={timeLeft.seconds} label="SEG" />
          </div>
        </div>
      </div>
    </div>
  );
}
