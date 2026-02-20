/**
 * DashboardLayout - Collapsible sidebar + backdrop-blur header
 *
 * Based on dashboard-react-para-launch design, rewritten with HeroUI v3.
 *
 * Features:
 * - Collapsible sidebar (256px -> 64px) with smooth 300ms transition
 * - Active nav item with gradient indicator bar
 * - Header with backdrop-blur and user avatar dropdown
 * - Flash message display
 * - Mobile: overlay sidebar
 */

import { useState } from 'react';
import { usePage, router } from '@inertiajs/react';
import type { ReactNode } from 'react';
import { Button as HeroButton } from '@heroui/react';
import { Bell, Menu } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { LanguageSelector } from '@/components/ui/LanguageSelector';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { FlashMessages } from '@/components/shared/FlashMessages';
import { SidebarHeader, SidebarNav, SidebarFooter, UserDropdown } from '@/components/layout';
import type { PageProps } from '@/types/inertia';

interface Props {
  children: ReactNode;
  title?: string;
}

export default function DashboardLayout({ children, title }: Props) {
  const { auth, flash } = usePage<PageProps>().props;
  const { url } = usePage();
  const { t } = useTranslation('common');
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const sidebarWidth = collapsed ? 'w-16' : 'w-64';
  const mainMargin = collapsed ? 'lg:ml-16' : 'lg:ml-64';

  return (
    <div className="flex h-screen bg-default-50 overflow-hidden">
      {/* -- Mobile overlay -- */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-background border-r border-divider flex flex-col animate-slide-in-left">
            <SidebarHeader collapsed={false} onToggle={() => setMobileOpen(false)} />
            <SidebarNav currentUrl={url} collapsed={false} onNavigate={() => setMobileOpen(false)} />
            <SidebarFooter user={auth.user} collapsed={false} />
          </aside>
        </div>
      )}

      {/* -- Desktop sidebar -- */}
      <aside
        className={`hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:z-40
          ${sidebarWidth} bg-background border-r border-divider transition-all duration-300`}
      >
        <SidebarHeader collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
        <SidebarNav currentUrl={url} collapsed={collapsed} />
        <SidebarFooter user={auth.user} collapsed={collapsed} />
      </aside>

      {/* -- Main content -- */}
      <div className={`flex-1 flex flex-col h-screen overflow-hidden transition-all duration-300 ${mainMargin}`}>
        {/* Header */}
        <header className="flex-shrink-0 h-16 z-30 border-b border-divider bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center px-6 gap-4">
          {/* Mobile hamburger */}
          <HeroButton
            variant="ghost"
            size="sm"
            isIconOnly
            onPress={() => setMobileOpen(true)}
            className="lg:hidden -ml-2 text-default-500 hover:text-foreground"
            aria-label={t('nav.aria.openMenu', 'Open menu')}
          >
            <Menu className="h-5 w-5" />
          </HeroButton>

          {/* Page title */}
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-foreground">{title}</h1>
          </div>

          {/* Right side controls */}
          <div className="flex items-center gap-1">
            <LanguageSelector />
            <ThemeToggle />

            {/* Notifications */}
            <HeroButton
              variant="ghost"
              size="sm"
              isIconOnly
              onPress={() => router.visit('/app/notifications/')}
              className="relative text-default-500"
              aria-label={t('nav.aria.notifications', 'Notifications')}
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2.5 w-2.5 rounded-full bg-danger animate-pulse" />
            </HeroButton>

            {/* User dropdown */}
            <UserDropdown user={auth.user} />
          </div>
        </header>

        {/* Flash messages */}
        <FlashMessages flash={flash} />

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6 space-y-6">{children}</main>
      </div>
    </div>
  );
}
