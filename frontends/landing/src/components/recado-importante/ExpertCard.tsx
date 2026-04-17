/**
 * Expert/instructor card with gradient border effect.
 *
 * Light gray card with red gradient border (CSS border-image trick).
 * Displays instructor photo, name, title, and social proof stats.
 */
interface ExpertCardProps {
  name: string;
  title: string;
  description: string;
  image?: string;
}

export default function ExpertCard({
  name,
  title,
  description,
  image,
}: ExpertCardProps) {
  return (
    <section className="bg-black px-4 py-12 md:py-16">
      <div className="mx-auto max-w-4xl">
        <div
          className="rounded-2xl p-[3px]"
          style={{
            backgroundImage:
              'linear-gradient(90deg, #7f1d1d, #991b1b, #dc2626, #ef4444)',
          }}
        >
          <div className="rounded-2xl bg-[#f5f5f5] p-6 md:p-10">
            <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
              {image && (
                <img
                  src={image}
                  alt={name}
                  className="h-32 w-32 flex-shrink-0 rounded-full object-cover md:h-40 md:w-40"
                  loading="lazy"
                />
              )}
              <div>
                <h3 className="text-2xl font-bold text-gray-900 md:text-3xl">
                  {name}
                </h3>
                <p className="mt-1 text-base font-medium text-red-600 md:text-lg">
                  {title}
                </p>
                <p className="mt-4 text-sm leading-relaxed text-gray-700 md:text-base">
                  {description}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
