/**
 * Reusable section component for legal pages (Terms, Privacy).
 *
 * Provides consistent heading + content styling across all legal documents.
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
      <h3 className="mb-2 text-base font-semibold text-gray-900">{title}</h3>
      {children}
    </section>
  );
}
