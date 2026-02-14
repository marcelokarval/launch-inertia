/**
 * Reusable section component for legal pages (Terms, Privacy).
 *
 * Dark theme: white headings on dark background.
 * Matches legacy Next.js termos-content.tsx styling.
 */
export default function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3 className="mb-2 text-lg font-semibold text-white">{title}</h3>
      {children}
    </section>
  );
}
