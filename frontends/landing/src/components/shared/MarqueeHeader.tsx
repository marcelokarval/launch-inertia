/**
 * Infinite scrolling marquee header bar.
 *
 * Renders repeating text items in a seamless horizontal loop.
 * Uses CSS translateX(-50%) on doubled content for seamless loop.
 *
 * @example
 * <MarqueeHeader
 *   items={['Compra Aprovada', 'Você é Aluno', 'Bem-Vindo']}
 *   bgColor="#1e3a8a"
 *   speed={30}
 * />
 */

interface MarqueeHeaderProps {
  /** Text items to scroll */
  items: string[];
  /** Separator between items */
  separator?: string;
  /** Background color (CSS value) */
  bgColor?: string;
  /** Animation duration in seconds (higher = slower) */
  speed?: number;
  /** Additional className for the outer container */
  className?: string;
}

export default function MarqueeHeader({
  items,
  separator = '•',
  bgColor = '#1e3a8a',
  speed = 30,
  className = '',
}: MarqueeHeaderProps) {
  // Duplicate items 8x for seamless loop across wide screens
  const repeated = Array.from({ length: 8 }, () => items).flat();

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 overflow-hidden py-2 md:py-2.5 ${className}`}
      style={{ backgroundColor: bgColor }}
    >
      <div
        className="flex w-max items-center whitespace-nowrap animate-marquee"
        style={{ animationDuration: `${speed}s` }}
      >
        {repeated.map((text, i) => (
          <span key={i} className="flex items-center">
            <span className="px-4 text-base font-bold text-white md:px-6 md:text-lg lg:text-xl">
              {text}
            </span>
            <span className="px-2 text-base text-white md:text-lg lg:text-xl">
              {separator}
            </span>
          </span>
        ))}
      </div>
    </header>
  );
}
