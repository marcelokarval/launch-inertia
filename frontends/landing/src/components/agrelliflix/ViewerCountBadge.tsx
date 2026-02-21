/**
 * Live viewer count badge — shows simulated viewer count.
 */
import { Eye } from 'lucide-react';

interface ViewerCountBadgeProps {
  count: number;
  redPrimary: string;
}

export default function ViewerCountBadge({ count, redPrimary }: ViewerCountBadgeProps) {
  return (
    <div
      className="flex items-center gap-1.5 px-3 py-1 rounded-full text-white text-sm font-medium"
      style={{ backgroundColor: redPrimary }}
    >
      <Eye size={14} />
      <span className="animate-pulse">●</span>
      <span>{count.toLocaleString()} assistindo</span>
    </div>
  );
}
