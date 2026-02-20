import { Chip } from '@heroui/react';
import type { Tag } from '@/types';

interface TagChipsProps {
  tags: Tag[];
}

export function TagChips({ tags }: TagChipsProps) {
  if (tags.length === 0) return null;

  return (
    <div className="flex gap-1 max-w-[160px]">
      {tags.slice(0, 2).map((tag) => (
        <Chip
          key={tag.id}
          size="sm"
          variant="soft"
          className="max-w-[75px] truncate text-[10px]"
          style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
        >
          {tag.name}
        </Chip>
      ))}
      {tags.length > 2 && (
        <Chip size="sm" variant="soft" color="default">
          +{tags.length - 2}
        </Chip>
      )}
    </div>
  );
}
