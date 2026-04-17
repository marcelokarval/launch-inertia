/**
 * LembreteBF (Black Friday Reminder) Page.
 *
 * Promotional page with countdown timer, course listings, bonus tiers,
 * pricing comparison, and urgency-driven CTAs. All content is config-driven
 * via Django Inertia props.
 *
 * Legacy: frontend-landing-pages/app/lembrete-bf/page.tsx (676 lines)
 */
import { Head } from '@inertiajs/react';

import {
  CountdownBanner,
  HeroSection,
  CourseCard,
  BonusSection,
  BenefitGrid,
  PricingSection,
  SummarySection,
  WarningSection,
} from '@/components/lembrete-bf';
import type { LembreteBFPageProps } from '@/types';

const DISCLAIMER =
  '*Aplicativos, Ferramentas, Imersão Presencial, Mentoria Individual, Master Agrelli, Bot Irei não estão incluídos nesta oferta.';

export default function LembreteBFPage({ config }: LembreteBFPageProps) {
  const {
    target_date,
    cta_link,
    cta_text,
    headline,
    benefits,
    courses,
    bonuses,
    normal_prices,
    special_price,
    installments_text,
    images,
  } = config;

  const handleCta = () => {
    window.location.href = cta_link;
  };

  return (
    <>
      <Head title="Black Friday Agrelli — Oferta Especial" />

      <div className="min-h-screen bg-black">
        {/* Fixed countdown banner */}
        <CountdownBanner targetDate={target_date} />

        {/* Hero: logo + headline + benefits + CTA */}
        <HeroSection
          logoUrl={images.logo}
          headline={headline}
          benefits={benefits}
          ctaText={cta_text}
          onCtaClick={handleCta}
          whatsappLink={cta_link}
          disclaimer={DISCLAIMER}
        />

        {/* Cross image divider */}
        {images.hero_cross && (
          <div className="w-full">
            <img
              src={images.hero_cross}
              alt=""
              className="h-auto w-full"
              aria-hidden="true"
            />
          </div>
        )}

        {/* Decision section */}
        <div className="bg-black px-4 py-8">
          <div className="mx-auto max-w-3xl space-y-4 text-center">
            <h2 className="text-2xl font-bold text-white md:text-3xl">
              A decisão mais fácil da sua vida
            </h2>
            <p className="text-base leading-relaxed text-white md:text-lg">
              Acho que você percebeu o tamanho da oportunidade. Com os bônus que
              eu preparei para essa oferta especial, fica praticamente impossível
              não querer fazer parte.
            </p>
            <p className="text-base leading-relaxed text-white md:text-lg">
              A nossa intenção é que essa seja uma decisão extremamente fácil
              para você.
            </p>
          </div>
        </div>

        {/* Courses section */}
        <div className="bg-black px-4 py-8">
          <div className="mx-auto max-w-4xl">
            <h2 className="mb-8 text-center text-xl font-bold text-white md:text-2xl">
              Quais cursos estão incluídos nesta oferta e quais ainda vão
              entrar?
            </h2>
            <div className="space-y-4">
              {courses.map((course) => (
                <CourseCard key={course.title} course={course} />
              ))}
            </div>
          </div>
        </div>

        {/* Bonuses */}
        <BonusSection bonuses={bonuses} />

        {/* Benefit checkmark grid */}
        <BenefitGrid benefits={benefits} />

        {/* Pricing comparison */}
        <PricingSection
          normalPrices={normal_prices}
          specialPrice={special_price}
          installmentsText={installments_text}
        />

        {/* Summary with bg + phone mockup */}
        <SummarySection
          bgImage={images.summary_bg}
          phoneMockup={images.phone_mockup}
          specialPrice={special_price}
          installmentsText={installments_text}
        />

        {/* Final CTA */}
        <div className="bg-black px-4 py-8">
          <div className="mx-auto max-w-2xl space-y-4 text-center">
            <button
              onClick={handleCta}
              className="w-full transform rounded-lg bg-[#FF2B5C] px-8 py-4 text-lg font-bold text-white shadow-lg transition-all duration-300 hover:scale-[1.02] hover:bg-[#E01B4C] hover:shadow-xl md:text-xl"
            >
              {cta_text}
            </button>
            <p className="text-xs text-white/60 md:text-sm">{DISCLAIMER}</p>
          </div>
        </div>

        {/* Warning section */}
        <WarningSection bgImage={images.warning_bg} />

        {/* Footer disclaimer */}
        <div className="bg-black px-4 py-8">
          <div className="mx-auto max-w-3xl text-center">
            <p className="mb-3 text-base text-white">
              O que não está incluso nesta oferta:
            </p>
            <p className="text-sm text-white/70">{DISCLAIMER}</p>
          </div>
        </div>
      </div>
    </>
  );
}
