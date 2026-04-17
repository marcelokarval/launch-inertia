/**
 * Bonus tiers section for the LembreteBF page.
 *
 * Displays scarcity-driven bonus tiers with highlighted tier numbers.
 */
import type { BFBonus } from '@/types';

interface BonusSectionProps {
  bonuses: BFBonus[];
}

export default function BonusSection({ bonuses }: BonusSectionProps) {
  return (
    <div className="bg-black px-4 py-8">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="mb-6 text-2xl font-bold text-white md:text-3xl">
          Além disso, alguns bônus{' '}
          <span className="text-[#FF2B5C]">exclusivos:</span>
        </h2>

        <div className="space-y-4 text-sm text-white md:text-base">
          {bonuses.map((bonus) => (
            <p key={bonus.tier}>
              Somente os{' '}
              <span className="font-bold text-[#FF2B5C]">{bonus.tier}</span>{' '}
              {bonus.description}
            </p>
          ))}
          <p className="text-lg font-bold">
            Não é desconto de mentira você nunca mais vai conseguir comprar com
            um desconto tão grande.
          </p>
        </div>
      </div>
    </div>
  );
}
