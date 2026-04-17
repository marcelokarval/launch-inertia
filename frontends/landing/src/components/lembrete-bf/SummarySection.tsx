/**
 * Summary section with background image, phone mockup, and price comparison cards.
 *
 * Shows two pricing tiers side by side (non-student vs student).
 */
interface SummarySectionProps {
  /** Background image URL */
  bgImage?: string;
  /** Phone mockup image URL */
  phoneMockup?: string;
  /** Special price text */
  specialPrice: string;
  /** Installments text */
  installmentsText: string;
}

export default function SummarySection({
  bgImage,
  phoneMockup,
  specialPrice,
  installmentsText,
}: SummarySectionProps) {
  return (
    <div className="relative px-4 py-12">
      {/* Background image */}
      {bgImage && (
        <div className="absolute inset-0 z-0">
          <img
            src={bgImage}
            alt=""
            className="h-full w-full object-cover"
            loading="lazy"
            aria-hidden="true"
          />
        </div>
      )}

      <div className="relative z-10 mx-auto max-w-4xl">
        <h2 className="mb-8 text-center text-2xl font-bold text-white md:text-3xl">
          Resumindo,{' '}
          <span className="text-[#FF2B5C]">
            nessa Black você vai ter acesso a todos os cursos online mais os
            Bônus acima pelo resto da vida:
          </span>
        </h2>

        <div className="mt-8 flex flex-col items-center justify-center gap-6 md:flex-row">
          {/* Phone mockup */}
          {phoneMockup && (
            <div className="flex-shrink-0">
              <img
                src={phoneMockup}
                alt="Preços"
                className="h-auto w-auto max-w-[200px]"
                loading="lazy"
              />
            </div>
          )}

          {/* Price cards side by side */}
          <div className="flex max-w-2xl flex-1 flex-col gap-4 sm:flex-row">
            <div className="flex-1 rounded-lg border-2 border-white bg-black/90 p-5">
              <h3 className="mb-3 text-lg font-bold text-white">Não aluno</h3>
              <p className="text-2xl font-bold text-white">
                {installmentsText}
              </p>
              <p className="mt-1 text-base text-white">
                à vista {specialPrice}
              </p>
            </div>

            <div className="flex-1 rounded-lg border-2 border-[#FF2B5C] bg-black/90 p-5">
              <h3 className="mb-3 text-lg font-bold text-white">
                Aluno de algum curso
              </h3>
              <p className="text-2xl font-bold text-[#FF2B5C]">
                12x de $89,00
              </p>
              <p className="mt-1 text-base text-white">à vista $797,00</p>
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-lg text-white">
          De: <span className="line-through">$19,076,00</span>
        </p>
        <p className="text-center text-xl font-bold text-white">
          Por apenas:
        </p>
      </div>
    </div>
  );
}
