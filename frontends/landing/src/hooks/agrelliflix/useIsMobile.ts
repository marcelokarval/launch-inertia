import { useState, useEffect } from 'react';

/**
 * Responsive breakpoint detection hook.
 *
 * @param breakpoint - Width threshold in pixels (default: 1024 = lg).
 * @returns true if viewport is narrower than breakpoint.
 */
export function useIsMobile(breakpoint: number = 1024): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < breakpoint);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, [breakpoint]);

  return isMobile;
}
