/**
 * 2x2 grid of benefit checkmark cards.
 *
 * Each card has a check icon and benefit text on dark bg.
 */
interface BenefitGridProps {
  benefits: string[];
}

export default function BenefitGrid({ benefits }: BenefitGridProps) {
  return (
    <div className="bg-black px-4 py-12">
      <div className="mx-auto max-w-5xl">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-5">
          {benefits.map((benefit) => (
            <div
              key={benefit}
              className="flex flex-row items-center gap-2 rounded-[20px] p-4"
              style={{ backgroundColor: '#232323' }}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                className="flex-shrink-0"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="12" fill="#FF2B5C" />
                <path
                  d="M7 12.5L10.5 16L17 9"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <p className="text-sm text-white md:text-base">{benefit}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
