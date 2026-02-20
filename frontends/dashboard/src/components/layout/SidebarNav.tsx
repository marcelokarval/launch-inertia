/**
 * SidebarNav — Main + secondary navigation groups with NavLink items.
 */

import { Link } from '@inertiajs/react';
import { Chip, Tooltip } from '@heroui/react';
import { useTranslation } from 'react-i18next';
import { mainNavItems, secondaryNavItems, isActive } from './sidebar-nav-config';
import type { NavItem } from './sidebar-nav-config';

interface SidebarNavProps {
  currentUrl: string;
  collapsed: boolean;
  onNavigate?: () => void;
}

export function SidebarNav({ currentUrl, collapsed, onNavigate }: SidebarNavProps) {
  const { t } = useTranslation('common');

  return (
    <nav className="flex-1 overflow-y-auto p-3 space-y-6">
      {/* Main */}
      <div className="space-y-1">
        {!collapsed && (
          <p className="px-3 mb-2 text-xs font-semibold text-default-400 uppercase tracking-wider">
            {t('nav.principal', 'Main')}
          </p>
        )}
        {mainNavItems.map((item) => (
          <NavLink
            key={item.key}
            item={item}
            currentUrl={currentUrl}
            collapsed={collapsed}
            onNavigate={onNavigate}
          />
        ))}
      </div>

      {/* Secondary */}
      <div className="space-y-1">
        {!collapsed && (
          <p className="px-3 mb-2 text-xs font-semibold text-default-400 uppercase tracking-wider">
            {t('nav.tools', 'Tools')}
          </p>
        )}
        {secondaryNavItems.map((item) => (
          <NavLink
            key={item.key}
            item={item}
            currentUrl={currentUrl}
            collapsed={collapsed}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </nav>
  );
}

// ── NavLink (internal) ──────────────────────────────────────────────────────

interface NavLinkProps {
  item: NavItem;
  currentUrl: string;
  collapsed: boolean;
  onNavigate?: () => void;
}

function NavLink({ item, currentUrl, collapsed, onNavigate }: NavLinkProps) {
  const { t } = useTranslation('common');
  const active = isActive(item.href, currentUrl);
  const label = t(`nav.${item.key}`, item.key);

  const content = (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
        ${active
          ? 'bg-gradient-primary text-white shadow-sm'
          : 'text-default-600 hover:bg-default-100 hover:text-foreground'
        }
        ${collapsed ? 'justify-center' : ''}
      `}
    >
      {/* Active indicator bar */}
      {active && !collapsed && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-background/80" />
      )}

      <item.icon className={`h-5 w-5 flex-shrink-0 ${active ? 'text-white' : ''}`} />

      {!collapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {item.badge && (
            <Chip
              size="sm"
              color={item.badge.color}
              variant="soft"
              className="text-[10px] h-5 min-w-0"
            >
              {t(item.badge.label, item.badge.label)}
            </Chip>
          )}
        </>
      )}
    </Link>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <Tooltip.Trigger>{content}</Tooltip.Trigger>
        <Tooltip.Content placement="right">{label}</Tooltip.Content>
      </Tooltip>
    );
  }
  return content;
}
