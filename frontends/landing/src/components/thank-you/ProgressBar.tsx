import { useEffect, useState } from 'react';

interface ProgressBarProps {
  /** Target percentage to animate to (0-100) */
  targetPercentage?: number;
  /** Animation duration in milliseconds */
  duration?: number;
  /** Step labels below the bar */
  steps?: { label: string; completed: boolean }[];
}

/**
 * Animated progress bar with optional step indicators.
 *
 * Animates from 0 to targetPercentage on mount.
 * Shows step indicators below for multi-step flows.
 */
export default function ProgressBar({
  targetPercentage = 90,
  duration = 2000,
  steps,
}: ProgressBarProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let rafId: number;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const pct = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - pct, 3);
      setProgress(eased * targetPercentage);

      if (pct < 1) {
        rafId = requestAnimationFrame(animate);
      }
    };
    rafId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(rafId);
  }, [targetPercentage, duration]);

  return (
    <div className="w-full">
      {/* Bar */}
      <div className="relative h-3 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-green-400 to-green-500 transition-[width] duration-100"
          style={{ width: `${progress}%` }}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 animate-[shimmer_2s_linear_infinite] bg-gradient-to-r from-transparent via-white/30 to-transparent" />
        </div>
      </div>

      {/* Percentage label */}
      <p className="mt-1 text-right text-xs font-medium text-gray-500">
        {Math.round(progress)}% completo
      </p>

      {/* Step indicators */}
      {steps && steps.length > 0 && (
        <div className="mt-3 flex justify-between">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-1 text-xs">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                  step.completed
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step.completed ? '\u2713' : i + 1}
              </span>
              <span className={step.completed ? 'font-medium text-green-700' : 'text-gray-500'}>
                {step.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
