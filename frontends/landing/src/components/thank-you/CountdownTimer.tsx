import { useEffect, useRef, useState } from 'react';

interface CountdownTimerProps {
  /** Total countdown duration in minutes */
  initialMinutes?: number;
  /** Callback when timer expires */
  onExpire?: () => void;
  /** Optional label above the timer */
  label?: string;
}

/**
 * Countdown timer — dark theme with urgency mode.
 *
 * Matches legacy `components/thank-you/countdown-timer.tsx`:
 * - Dark bg-gray-800 boxes with border-gray-700
 * - Turns red (bg-red-600 + border-red-400) in last 60s
 * - Pulsing colon separator
 * - "OFERTA EXPIRA EM:" label in yellow
 * - Urgency message in last seconds
 */
export default function CountdownTimer({
  initialMinutes = 15,
  onExpire,
  label,
}: CountdownTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState(initialMinutes * 60);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onExpireRef.current?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const isUrgent = secondsLeft <= 60 && secondsLeft > 0;
  const isExpired = secondsLeft <= 0;

  return (
    <div className="space-y-2 text-center md:space-y-4">
      {/* Label */}
      <p
        className={`text-sm font-semibold md:text-lg ${
          isUrgent ? 'animate-pulse text-red-400' : 'text-yellow-400'
        }`}
      >
        {isExpired
          ? 'TEMPO ESGOTADO!'
          : label || 'OFERTA EXPIRA EM:'}
      </p>

      {/* Timer display */}
      <div className="flex justify-center gap-2 md:gap-4">
        {/* Minutes */}
        <div
          className={`flex h-20 w-20 flex-col items-center justify-center rounded-lg border-2 shadow-xl sm:h-24 sm:w-24 md:h-32 md:w-32 ${
            isUrgent
              ? 'border-red-400 bg-red-600'
              : 'border-gray-700 bg-gray-800'
          }`}
        >
          <span className="text-2xl font-bold text-white sm:text-3xl md:text-5xl">
            {String(minutes).padStart(2, '0')}
          </span>
          <span className="text-[10px] uppercase text-gray-400 sm:text-xs md:text-sm">
            Minutos
          </span>
        </div>

        {/* Separator */}
        <div className="flex items-center text-2xl font-bold text-white sm:text-4xl md:text-6xl">
          <span className="animate-blink">:</span>
        </div>

        {/* Seconds */}
        <div
          className={`flex h-20 w-20 flex-col items-center justify-center rounded-lg border-2 shadow-xl sm:h-24 sm:w-24 md:h-32 md:w-32 ${
            isUrgent
              ? 'border-red-400 bg-red-600'
              : 'border-gray-700 bg-gray-800'
          }`}
        >
          <span className="text-2xl font-bold text-white sm:text-3xl md:text-5xl">
            {String(seconds).padStart(2, '0')}
          </span>
          <span className="text-[10px] uppercase text-gray-400 sm:text-xs md:text-sm">
            Segundos
          </span>
        </div>
      </div>

      {/* Urgency message */}
      {isUrgent && !isExpired && (
        <p className="animate-pulse font-semibold text-red-400">
          ÚLTIMOS SEGUNDOS! NÃO PERCA ESTA OPORTUNIDADE!
        </p>
      )}

      {/* Expired message */}
      {isExpired && (
        <div className="rounded-lg bg-red-600 p-4 text-white">
          <p className="font-bold">O tempo acabou!</p>
          <p className="mt-2 text-sm">
            Clique no botão acima AGORA para não perder sua vaga!
          </p>
        </div>
      )}
    </div>
  );
}
