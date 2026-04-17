/**
 * Course modules grid.
 *
 * Displays course module cards in a responsive grid (1 col mobile, 3 col desktop).
 * Each module shows title and description.
 */
import type { CourseModule } from '@/types';

interface ModulesGridProps {
  modules: CourseModule[];
}

export default function ModulesGrid({ modules }: ModulesGridProps) {
  if (!modules.length) return null;

  return (
    <section className="bg-[#0A0A0A] px-4 py-12 md:py-16">
      <div className="mx-auto max-w-5xl">
        <h2 className="mb-8 text-center text-2xl font-bold text-white md:text-3xl">
          O que você vai aprender
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {modules.map((mod, i) => (
            <div
              key={mod.title}
              className="rounded-xl border border-white/10 bg-zinc-900 p-5"
            >
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-red-600 text-sm font-bold text-white">
                {i + 1}
              </div>
              <h3 className="mb-2 text-base font-bold text-white md:text-lg">
                {mod.title}
              </h3>
              <p className="text-sm leading-relaxed text-white/60">
                {mod.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
