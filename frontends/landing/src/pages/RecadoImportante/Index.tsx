/**
 * RecadoImportante (Long-Form Sales / VSL) Page.
 *
 * Vertical sales letter with hero video, expert card, testimonials,
 * course modules, bonuses, pricing reveal, and floating CTA. All content
 * is config-driven via Django Inertia props.
 *
 * Legacy: frontend-landing-pages/app/recado-importante/ (~2,800 lines across 27 files)
 */
import { Head } from '@inertiajs/react';
import DOMPurify from 'dompurify';

import {
  SalesHeader,
  HeroVideo,
  ExpertCard,
  VideoGrid,
  ModulesGrid,
  BonusCard,
  PricingReveal,
  FloatingCTA,
} from '@/components/recado-importante';
import WhatsAppFloatingButton from '@/components/WhatsAppFloatingButton';
import type { RecadoImportantePageProps } from '@/types';

export default function RecadoImportantePage({
  config,
}: RecadoImportantePageProps) {
  const {
    video_id,
    cta_link,
    cta_text,
    target_date,
    expert,
    testimonials,
    course_description,
    modules,
    bonuses,
    mega_bonus,
    pricing,
    images,
  } = config;

  return (
    <>
      <Head title="Recado Importante — Arthur Agrelli" />

      {/* Fixed header with countdown */}
      <SalesHeader targetDate={target_date} />

      {/* 1. Hero — BG image + video + CTA */}
      <HeroVideo
        videoId={video_id}
        bgImage={images?.hero_bg}
        ctaLink={cta_link}
        ctaText={cta_text}
      />

      {/* 2. "What is it?" — course description text */}
      {course_description && (
        <section className="bg-[#0A0A0A] px-4 py-12 md:py-16">
          <div className="mx-auto max-w-4xl text-center">
            <div
              className="prose prose-invert mx-auto text-base leading-relaxed text-white/80 md:text-lg"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(course_description) }}
            />
          </div>
        </section>
      )}

      {/* 3. Expert card */}
      <ExpertCard
        name={expert.name}
        title={expert.title}
        description={expert.description}
        image={expert.image}
      />

      {/* 4. Video testimonials */}
      {testimonials.length > 0 && (
        <VideoGrid testimonials={testimonials} />
      )}

      {/* 5. Course map intro */}
      <section className="bg-[#7f1d1d] px-4 py-8 md:py-12">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-bold text-white md:text-3xl">
            Veja tudo que você vai aprender
          </h2>
          {images?.course_map && (
            <img
              src={images.course_map}
              alt="Mapa do curso"
              className="mt-6 h-auto w-full rounded-lg"
              loading="lazy"
            />
          )}
        </div>
      </section>

      {/* 6. Course modules grid */}
      <ModulesGrid modules={modules} />

      {/* 7. Bonuses */}
      {bonuses.length > 0 && (
        <section className="bg-black px-4 py-12 md:py-16">
          <div className="mx-auto max-w-4xl">
            <h2 className="mb-8 text-center text-2xl font-bold text-white md:text-3xl">
              Bônus{' '}
              <span className="text-red-500">exclusivos</span>
            </h2>
            <div className="space-y-4">
              {bonuses.map((bonus, i) => (
                <BonusCard key={bonus.title} bonus={bonus} index={i} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* 8. Mega bonus */}
      {mega_bonus && (
        <section className="bg-[#0A0A0A] px-4 py-12 md:py-16">
          <div className="mx-auto max-w-4xl">
            <div
              className="rounded-2xl p-[3px]"
              style={{
                backgroundImage:
                  'linear-gradient(90deg, #7f1d1d, #991b1b, #dc2626, #ef4444)',
              }}
            >
              <div className="rounded-2xl bg-[#f5f5f5] p-6 text-center md:p-10">
                <span className="inline-block rounded bg-red-600 px-3 py-1 text-xs font-bold uppercase text-white">
                  MEGA BÔNUS
                </span>
                <h3 className="mt-4 text-2xl font-bold text-gray-900 md:text-3xl">
                  {mega_bonus.title}
                </h3>
                <p className="mt-3 text-base text-gray-700 md:text-lg">
                  {mega_bonus.description}
                </p>
                {mega_bonus.value && (
                  <p className="mt-2 text-sm font-medium text-red-600">
                    Valor: {mega_bonus.value}
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 9. Urgency alert */}
      <section className="bg-[#7f1d1d] px-4 py-6 md:py-8">
        <div className="mx-auto max-w-4xl text-center">
          <p className="text-lg font-bold text-white md:text-xl">
            ⚠️ Atenção: As vagas são limitadas e esta oferta pode sair do ar a
            qualquer momento.
          </p>
        </div>
      </section>

      {/* 10. Pricing reveal */}
      <PricingReveal
        originalPrice={pricing.original_price}
        currentPrice={pricing.current_price}
        installmentsText={pricing.installments_text}
        discountText={pricing.discount_text}
        ctaLink={cta_link}
        ctaText={cta_text}
      />

      {/* Footer */}
      <footer className="bg-black px-4 py-8 md:py-12">
        <div className="mx-auto max-w-4xl text-center">
          <p className="text-sm text-white/40">
            © {new Date().getFullYear()} Arthur Agrelli. Todos os direitos
            reservados.
          </p>
          <p className="mt-2 text-xs text-white/30">
            Este site não é afiliado ao Facebook, Google ou qualquer entidade do
            Facebook/Google Inc. As informações contidas neste site são de
            caráter meramente informativo.
          </p>
        </div>
      </footer>

      {/* Floating CTA (appears after scroll) */}
      <FloatingCTA href={cta_link} text={cta_text} />

      {/* WhatsApp button */}
      <WhatsAppFloatingButton variant="green" mode="whatsapp" href={cta_link} />
    </>
  );
}
