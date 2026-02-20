/**
 * Confidence score badge — shared across Identity pages.
 *
 * Displays a coloured HeroUI Chip (green/yellow/red) with a shield icon
 * and the confidence percentage.
 */

import { Chip } from '@heroui/react'
import { Shield } from 'lucide-react'

interface ConfidenceBadgeProps {
  score: number
}

export function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const pct = Math.round(score * 100)
  const chipColor: 'success' | 'warning' | 'danger' =
    pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger'

  return (
    <Chip color={chipColor} variant="soft" size="sm">
      <span className="inline-flex items-center gap-1">
        <Shield className="w-3.5 h-3.5" />
        {pct}%
      </span>
    </Chip>
  )
}
