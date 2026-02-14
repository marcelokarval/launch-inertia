/**
 * RedBanner — Urgency banner at the top of thank-you pages.
 *
 * Full-width red banner with pulsing bold text.
 * Matches legacy `components/thank-you-us/red-banner.tsx`.
 */
export default function RedBanner({ text }: { text?: string }) {
  return (
    <div className="w-full bg-red-600 py-6 text-center md:py-8">
      <p className="animate-pulse px-4 text-base font-bold text-white md:text-xl lg:text-2xl">
        {text ||
          'N\u00c3O FECHE ESTA P\u00c1GINA ANTES DE ENTRAR NO GRUPO VIP DA MENTORIA GRATUITA. ESTA P\u00c1GINA N\u00c3O APARECER\u00c1 NOVAMENTE.'}
      </p>
    </div>
  );
}
