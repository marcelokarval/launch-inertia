/**
 * Bonus card for the sales page.
 *
 * Shows bonus title, description, value badge, and optional image.
 * Red accent color theme.
 */
import type { SalesBonus } from '@/types';

interface BonusCardProps {
  bonus: SalesBonus;
  index: number;
}

export default function BonusCard({ bonus, index }: BonusCardProps) {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-white/10 bg-zinc-900 p-5 md:flex-row md:items-start">
      {bonus.image && (
        <img
          src={bonus.image}
          alt={bonus.title}
          className="h-24 w-24 flex-shrink-0 rounded-lg object-cover"
          loading="lazy"
        />
      )}
      <div className="flex-1">
        <div className="mb-2 flex items-center gap-2">
          <span className="rounded bg-red-600 px-2 py-0.5 text-xs font-bold text-white">
            BÔNUS #{index + 1}
          </span>
          {bonus.value && (
            <span className="text-xs font-medium text-red-400">
              Valor: {bonus.value}
            </span>
          )}
        </div>
        <h3 className="mb-1 text-base font-bold text-white md:text-lg">
          {bonus.title}
        </h3>
        <p className="text-sm leading-relaxed text-white/60">
          {bonus.description}
        </p>
      </div>
    </div>
  );
}
