import { Head } from '@inertiajs/react';
import LandingLayout from '@/layouts/LandingLayout';
import type { HomeProps } from '@/types';

export default function HomeIndex({ title, description }: HomeProps) {
  return (
    <LandingLayout>
      <Head title={title} />
      <div className="flex min-h-[80vh] items-center justify-center">
        <div className="mx-auto max-w-[var(--max-width-form)] px-6 text-center animate-fade-in">
          <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)]">
            {title}
          </h1>
          <p className="mt-4 text-lg text-[var(--color-text-secondary)]">
            {description}
          </p>
          <div className="mt-8 inline-flex items-center gap-2 rounded-full bg-[var(--color-brand-primary)]/10 px-4 py-2 text-sm font-medium text-[var(--color-brand-primary)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-brand-primary)] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-brand-primary)]" />
            </span>
            Landing Pages — Online
          </div>
        </div>
      </div>
    </LandingLayout>
  );
}
