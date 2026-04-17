/**
 * Warning section with background image overlay.
 *
 * "ATENÇÃO" call-out warning that the offer may not repeat.
 */
interface WarningSectionProps {
  /** Background image URL */
  bgImage?: string;
}

export default function WarningSection({ bgImage }: WarningSectionProps) {
  return (
    <div className="relative px-4 py-12">
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

      <div className="relative z-10 mx-auto max-w-2xl text-center">
        <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
          ATENÇÃO
        </h2>
        <p className="mb-3 text-xl font-bold text-white md:text-2xl">
          Essa oferta Não Tem previsão para se repetir.
        </p>
        <p className="text-lg text-white md:text-xl">
          Você pode comprar depois… mas não seria inteligente da sua parte.
        </p>
      </div>
    </div>
  );
}
