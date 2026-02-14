import { useEffect, useState } from 'react';

interface ProgressBarProps {
  /** Target percentage to animate to (0-100). Default: 90 */
  targetPercentage?: number;
  /** Step labels below the bar */
  steps?: { label: string; completed: boolean }[];
}

/**
 * Animated progress bar — red gradient with diagonal stripes and shimmer.
 *
 * Matches legacy `components/thank-you-us/progress-bar.tsx`:
 * - Red gradient fill (#dc2626 -> #ef4444 -> #dc2626)
 * - Diagonal stripe overlay (repeating-linear-gradient 45deg)
 * - Shimmer animation on fill
 * - Percentage counter INSIDE the bar (right-aligned)
 * - 80% width container (w-4/5), left-aligned
 * - Dark bg-gray-700 track
 *
 * Uses CSS classes from globals.css (.progress-bar-fill).
 */
export default function ProgressBar({
  targetPercentage = 90,
  steps,
}: ProgressBarProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let current = 0;
    const interval = setInterval(() => {
      current += 2;
      if (current >= targetPercentage) {
        setProgress(targetPercentage);
        clearInterval(interval);
      } else {
        setProgress(current);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [targetPercentage]);

  return (
    <div className="w-full">
      {/* Container at 80% width — left-aligned like legacy */}
      <div className="w-4/5">
        <div className="relative h-6 w-full overflow-hidden rounded-full bg-gray-700">
          <div
            className="progress-bar-fill flex h-full items-center justify-end pr-2 transition-[width] duration-300 ease-out"
            style={{ width: `${progress}%` }}
          >
            {/* Percentage inside the bar */}
            {progress > 0 && (
              <span className="relative z-10 text-xs font-bold text-white">
                {Math.round(progress)}%
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Step indicators (optional) */}
      {steps && steps.length > 0 && (
        <div className="mt-3 flex justify-between">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-1 text-xs">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                  step.completed
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-600 text-gray-400'
                }`}
              >
                {step.completed ? '\u2713' : i + 1}
              </span>
              <span
                className={
                  step.completed
                    ? 'font-medium text-green-400'
                    : 'text-gray-400'
                }
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
