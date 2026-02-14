import { memo, useMemo, useState } from 'react';

import { IconChevronDown, IconHelpCircle, IconSearch } from '@/components/ui/icons';
import type { FAQItem } from '@/types';

interface FAQPanelProps {
  items: FAQItem[];
  categories: string[];
  className?: string;
}

/**
 * FAQ accordion panel with search and category filtering.
 *
 * Uses CSS transitions (no framer-motion dependency).
 * Supports multiple items open simultaneously.
 */
export default function FAQPanel({ items, categories, className = '' }: FAQPanelProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const toggleItem = (id: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const filteredItems = useMemo(
    () =>
      items.filter((item) => {
        const matchesSearch =
          searchQuery === '' ||
          item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.answer.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCategory = selectedCategory === null || item.category === selectedCategory;
        return matchesSearch && matchesCategory;
      }),
    [items, searchQuery, selectedCategory],
  );

  return (
    <div
      className={`flex min-h-0 flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 ${className}`}
    >
      {/* Header */}
      <div className="shrink-0 border-b border-zinc-700 bg-zinc-800/50 p-4">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-500 to-amber-700">
            <IconHelpCircle className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Perguntas Frequentes</h3>
            <p className="text-xs text-gray-400">Encontre respostas rápidas</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar pergunta..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-zinc-700 bg-zinc-800 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-gray-500 focus:border-amber-500/50 focus:outline-none"
          />
        </div>

        {/* Category filter */}
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              selectedCategory === null
                ? 'bg-amber-600 text-white'
                : 'bg-zinc-800 text-gray-400 hover:bg-zinc-700'
            }`}
          >
            Todos
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-amber-600 text-white'
                  : 'bg-zinc-800 text-gray-400 hover:bg-zinc-700'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* FAQ list */}
      <div className="custom-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
        {filteredItems.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            <IconHelpCircle className="mx-auto mb-3 h-12 w-12 opacity-50" />
            <p>Nenhuma pergunta encontrada</p>
            <p className="mt-1 text-sm">Tente outro termo de busca</p>
          </div>
        ) : (
          filteredItems.map((item) => (
            <FAQItemComponent
              key={item.id}
              item={item}
              isOpen={openItems.has(item.id)}
              onToggle={() => toggleItem(item.id)}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="shrink-0 border-t border-zinc-700 bg-zinc-800/30 p-4">
        <p className="text-center text-xs text-gray-500">
          Não encontrou sua dúvida? Fale conosco no chat ao lado
        </p>
      </div>
    </div>
  );
}

/** Single FAQ accordion item */
const FAQItemComponent = memo(function FAQItemComponent({
  item,
  isOpen,
  onToggle,
}: {
  item: FAQItem;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 transition-colors hover:border-zinc-700">
      <button onClick={onToggle} className="flex w-full items-center justify-between p-4 text-left">
        <span className="pr-4 font-medium text-white">{item.question}</span>
        <IconChevronDown
          className={`h-5 w-5 shrink-0 text-gray-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      <div
        className={`grid transition-[grid-template-rows] duration-200 ${
          isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div className="overflow-hidden">
          <div className="px-4 pb-4">
            <p className="text-sm leading-relaxed text-gray-400">{item.answer}</p>
          </div>
        </div>
      </div>
    </div>
  );
});
