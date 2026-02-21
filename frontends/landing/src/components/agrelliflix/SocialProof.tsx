/**
 * Social proof section — stats strip + rotating testimonials.
 */
import { useState, useEffect } from 'react';
import { Star, Users, DollarSign, TrendingUp } from 'lucide-react';

import type { AgrelliflixSocialProofConfig, AgrelliflixThemeConfig } from '@/types';

interface SocialProofProps {
  config: AgrelliflixSocialProofConfig;
  theme: AgrelliflixThemeConfig;
}

export default function SocialProof({ config, theme }: SocialProofProps) {
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const testimonials = config.testimonials;

  useEffect(() => {
    if (testimonials.length <= 1) return;
    const interval = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [testimonials.length]);

  if (!config.enabled) return null;

  const stats = config.stats;

  return (
    <div className="space-y-6">
      {/* Stats strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<Users size={20} />} value={`${stats.total_students.toLocaleString()}+`} label="Alunos" theme={theme} />
        <StatCard icon={<DollarSign size={20} />} value={`$${stats.average_profit.toLocaleString()}`} label="Lucro medio" theme={theme} />
        <StatCard icon={<TrendingUp size={20} />} value={`${stats.success_rate}%`} label="Taxa de sucesso" theme={theme} />
        <StatCard icon={<Star size={20} />} value={stats.rating.toString()} label="Avaliacao" theme={theme} />
      </div>

      {/* Testimonial carousel */}
      {testimonials.length > 0 && (
        <div className="rounded-lg p-4" style={{ backgroundColor: theme.grey_dark }}>
          <div className="flex items-start gap-3">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
              style={{ backgroundColor: theme.red_primary }}
            >
              {testimonials[activeTestimonial].name.charAt(0)}
            </div>
            <div className="flex-1">
              <p className="text-white/90 text-sm italic">
                &ldquo;{testimonials[activeTestimonial].text}&rdquo;
              </p>
              <p className="text-white/50 text-xs mt-1">
                {testimonials[activeTestimonial].name} — {testimonials[activeTestimonial].location}
              </p>
            </div>
          </div>
          {/* Dots */}
          <div className="flex gap-1 justify-center mt-3">
            {testimonials.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setActiveTestimonial(i)}
                className="w-1.5 h-1.5 rounded-full transition-all"
                style={{
                  backgroundColor: i === activeTestimonial ? theme.red_primary : 'rgba(255,255,255,0.2)',
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  value,
  label,
  theme,
}: {
  icon: React.ReactNode;
  value: string;
  label: string;
  theme: AgrelliflixThemeConfig;
}) {
  return (
    <div
      className="rounded-lg p-3 text-center"
      style={{ backgroundColor: theme.grey_dark }}
    >
      <div className="flex justify-center mb-1" style={{ color: theme.gold_accent }}>
        {icon}
      </div>
      <p className="text-white font-bold text-lg">{value}</p>
      <p className="text-white/50 text-xs">{label}</p>
    </div>
  );
}
