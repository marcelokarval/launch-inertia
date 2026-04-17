/**
 * Pricing reveal section.
 *
 * Shows original price crossed out, discount callout, and final price/installments.
 * Includes CTA button.
 */
interface PricingRevealProps {
  originalPrice: string;
  currentPrice: string;
  installmentsText: string;
  discountText: string;
  ctaLink: string;
  ctaText: string;
}

export default function PricingReveal({
  originalPrice,
  currentPrice,
  installmentsText,
  discountText,
  ctaLink,
  ctaText,
}: PricingRevealProps) {
  return (
    <section className="bg-black px-4 py-12 md:py-16">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="mb-6 text-2xl font-bold text-white md:text-3xl">
          E quanto custa tudo isso?
        </h2>

        {/* Original price struck through */}
        <p className="text-lg text-white/60 md:text-xl">
          De:{' '}
          <span className="text-2xl line-through md:text-3xl">
            {originalPrice}
          </span>
        </p>

        {/* Discount callout */}
        <div className="my-6 inline-block rounded-lg bg-red-600 px-6 py-3">
          <p className="text-base font-bold text-white md:text-lg">
            {discountText}
          </p>
        </div>

        {/* Current price */}
        <p className="text-3xl font-bold text-white md:text-5xl">
          {currentPrice}
        </p>
        <p className="mt-2 text-base text-white/80 md:text-lg">
          {installmentsText}
        </p>

        {/* CTA */}
        <a
          href={ctaLink}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-8 inline-block w-full max-w-md transform rounded-xl bg-green-500 px-8 py-4 text-lg font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:bg-green-600 hover:shadow-xl md:text-xl"
        >
          {ctaText}
        </a>
      </div>
    </section>
  );
}
