/**
 * Hero section for the LembreteBF page.
 *
 * Logo, main headline with highlighted text, benefits list, and CTA button.
 * Background: gradient from black via red-950/20 to black.
 */
interface HeroSectionProps {
  /** Logo image URL */
  logoUrl: string;
  /** Full headline (plain text — highlight is rendered inline) */
  headline: string;
  /** Benefits list items */
  benefits: string[];
  /** CTA button text */
  ctaText: string;
  /** CTA click handler */
  onCtaClick: () => void;
  /** WhatsApp doubts link */
  whatsappLink?: string;
  /** Disclaimer text below CTA */
  disclaimer?: string;
}

export default function HeroSection({
  logoUrl,
  headline,
  benefits,
  ctaText,
  onCtaClick,
  whatsappLink,
  disclaimer,
}: HeroSectionProps) {
  return (
    <div className="relative bg-gradient-to-b from-black via-red-950/20 to-black px-4 pb-12 pt-32 md:pt-28">
      <div className="mx-auto max-w-3xl space-y-6 text-center">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <img
            src={logoUrl}
            alt="Black Friday Agrelli"
            className="h-auto w-auto max-w-[200px]"
            loading="eager"
          />
        </div>

        {/* Headline — split on the first occurrence of text wrapped in *asterisks* for highlight */}
        <h1
          className="text-2xl font-bold leading-tight text-white md:text-4xl"
          dangerouslySetInnerHTML={{ __html: headline }}
        />

        {/* Benefits */}
        <div className="mx-auto max-w-xl space-y-3 pt-6 text-left text-base text-white md:text-lg">
          <p className="font-bold">
            Quem aproveitar esta oportunidade histórica terá:
          </p>
          <ul className="space-y-2 pl-4">
            {benefits.map((benefit) => (
              <li key={benefit}>✓ {benefit}</li>
            ))}
          </ul>
        </div>

        {/* CTA */}
        <button
          onClick={onCtaClick}
          className="mx-auto mt-6 w-full max-w-md transform rounded-lg bg-[#FF2B5C] px-8 py-4 text-lg font-bold text-white shadow-lg transition-all duration-300 hover:scale-[1.02] hover:bg-[#E01B4C] hover:shadow-xl md:text-xl"
        >
          {ctaText}
        </button>

        {disclaimer && (
          <p className="mt-3 text-xs text-white/60 md:text-sm">{disclaimer}</p>
        )}

        {/* WhatsApp link */}
        {whatsappLink && (
          <>
            <a
              href={whatsappLink}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block text-sm text-white underline transition-colors hover:text-[#FF2B5C] md:text-base"
            >
              Tirar minhas dúvidas via WhatsApp**
            </a>
            <p className="text-xs text-white/60">
              **Normalmente respondemos em menos de 5 minutos
            </p>
          </>
        )}
      </div>
    </div>
  );
}
