/**
 * SidebarHeader — Brand logo + collapse toggle.
 */

import { Link } from '@inertiajs/react';
import { Button as HeroButton } from '@heroui/react';
import { Rocket, ChevronLeft } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface Props {
  collapsed: boolean;
  onToggle: () => void;
}

export function SidebarHeader({ collapsed, onToggle }: Props) {
  const { t } = useTranslation('common');
  return (
    <div className="h-16 flex items-center justify-between px-4 border-b border-divider flex-shrink-0">
      <Link href="/app/" className="flex items-center gap-2.5 overflow-hidden">
        <div className="h-8 w-8 rounded-lg bg-gradient-primary flex items-center justify-center flex-shrink-0">
          <Rocket className="h-4.5 w-4.5 text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <span className="text-lg font-bold text-foreground">Launch</span>
            <span className="text-xs text-default-400 ml-1.5">v2.0</span>
          </div>
        )}
      </Link>
      <HeroButton
        variant="ghost"
        size="sm"
        isIconOnly
        onPress={onToggle}
        className="hidden lg:flex text-default-400 hover:text-foreground"
        aria-label={collapsed ? t('nav.aria.expandSidebar', 'Expand sidebar') : t('nav.aria.collapseSidebar', 'Collapse sidebar')}
      >
        <ChevronLeft className={`h-4 w-4 transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
      </HeroButton>
    </div>
  );
}
