/**
 * Pricing comparison section for the LembreteBF page.
 *
 * Shows two price tables: normal value (dark bg) and special offer (gradient bg).
 */
import type { BFPriceEntry } from '@/types';

interface PricingSectionProps {
  normalPrices: BFPriceEntry[];
  /** à vista price for the special offer */
  specialPrice: string;
  installmentsText: string;
}

function PriceRow({
  entry,
  borderColor = 'border-gray-700',
}: {
  entry: BFPriceEntry;
  borderColor?: string;
}) {
  return (
    <div className={`flex justify-between border-b py-1 ${borderColor}`}>
      <span>{entry.label}</span>
      <span>{entry.value}</span>
    </div>
  );
}

export default function PricingSection({
  normalPrices,
  specialPrice,
  installmentsText,
}: PricingSectionProps) {
  // Compute total for the normal prices table
  const total = normalPrices.reduce((sum, entry) => {
    const num = parseFloat(entry.value.replace(/[$,]/g, '').replace('.', ''));
    return Number.isNaN(num) ? sum : sum + num;
  }, 0);

  const formattedTotal =
    total > 0
      ? `$${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
      : 'Incalculável';

  return (
    <div className="bg-black px-4 py-8">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="mb-8 text-2xl font-bold text-white md:text-3xl">
          E o preço?
        </h2>

        {/* Normal value table */}
        <div className="mb-6 rounded-lg bg-gray-900/50 p-6">
          <h3 className="mb-4 text-xl font-bold text-white">Valor normal</h3>
          <div className="space-y-2 text-sm text-white">
            {normalPrices.map((entry) => (
              <PriceRow key={entry.label} entry={entry} />
            ))}
            <div className="mt-2 flex justify-between border-t-2 border-gray-600 pt-3 text-lg font-bold">
              <span>Total</span>
              <span className="text-[#FF2B5C]">{formattedTotal}</span>
            </div>
          </div>
        </div>

        {/* Special offer table */}
        <div className="mb-6 rounded-lg bg-gradient-to-r from-[#FF2B5C] to-[#FF5C7C] p-6">
          <h3 className="mb-2 text-xl font-bold text-white">
            VALOR DA OFERTA INSANA E ESPECIAL
          </h3>
          <p className="mb-4 text-xs text-white">
            Válido Somente até o encerramento da Black Friday
          </p>

          <div className="space-y-2 text-sm text-white">
            {normalPrices.map((entry) => (
              <PriceRow
                key={entry.label}
                entry={entry}
                borderColor="border-white/20"
              />
            ))}
          </div>

          <p className="mt-4 text-base text-white md:text-lg">
            Você leva TUDO ISSO para SEMPRE pagando apenas o{' '}
            <span className="font-bold">pequeno preço</span> de{' '}
            {installmentsText}
            {specialPrice && (
              <span className="block text-sm opacity-80">
                ou {specialPrice} à vista
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
