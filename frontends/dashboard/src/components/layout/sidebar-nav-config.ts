/**
 * Sidebar navigation configuration — shared between layout sub-components.
 */

import {
  Home,
  Users,
  Target,
  Zap,
  Calendar,
  BarChart3,
  CreditCard,
  Bell,
  Settings,
} from 'lucide-react';
import type { PageProps } from '@/types/inertia';

export interface NavItem {
  key: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: { label: string; color: 'default' | 'warning' | 'accent' | 'success' };
}

export const mainNavItems: NavItem[] = [
  { key: 'dashboard', href: '/app/', icon: Home },
  { key: 'identities', href: '/app/identities/', icon: Users },
  { key: 'campaigns', href: '#', icon: Target, badge: { label: 'nav.badges.soon', color: 'warning' } },
  { key: 'automations', href: '#', icon: Zap, badge: { label: 'nav.badges.pro', color: 'accent' } },
  { key: 'schedule', href: '#', icon: Calendar },
  { key: 'reports', href: '#', icon: BarChart3 },
];

export const secondaryNavItems: NavItem[] = [
  { key: 'billing', href: '/app/billing/', icon: CreditCard },
  { key: 'notifications', href: '/app/notifications/', icon: Bell },
  { key: 'settings', href: '/app/settings/', icon: Settings },
];

export function isActive(href: string, currentUrl: string): boolean {
  if (href === '#') return false;
  if (href === '/app/') return currentUrl === '/app/' || currentUrl === '/';
  return currentUrl.startsWith(href);
}

export type SidebarUser = PageProps['auth']['user'];
