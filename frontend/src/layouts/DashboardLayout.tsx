/**
 * DashboardLayout - Collapsible sidebar + backdrop-blur header
 *
 * Based on dashboard-react-para-launch design, rewritten with HeroUI v3.
 *
 * Features:
 * - Collapsible sidebar (256px → 64px) with smooth 300ms transition
 * - Active nav item with gradient indicator bar
 * - Header with backdrop-blur and user avatar dropdown
 * - Flash message display
 * - Mobile: overlay sidebar
 */

import { useState } from 'react'
import { Link, usePage, router } from '@inertiajs/react'
import type { ReactNode } from 'react'
import { Avatar, Chip, Dropdown } from '@heroui/react'
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
  HelpCircle,
  LogOut,
  Menu,
  ChevronLeft,
  Rocket,
  ChevronDown,
  Sun,
  Moon,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { LanguageSelector } from '@/components/ui/LanguageSelector'
import { useTheme } from '@/hooks/useTheme'
import type { PageProps } from '@/types/inertia'

// ============================================================================
// Types & Config
// ============================================================================

interface Props {
  children: ReactNode
  title?: string
}

interface NavItem {
  key: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: { label: string; color: 'default' | 'warning' | 'accent' | 'success' }
}

const mainNavItems: NavItem[] = [
  { key: 'dashboard', href: '/dashboard/', icon: Home },
  { key: 'contacts', href: '/contacts/', icon: Users },
  { key: 'campaigns', href: '#', icon: Target, badge: { label: 'Soon', color: 'warning' } },
  { key: 'automations', href: '#', icon: Zap, badge: { label: 'Pro', color: 'accent' } },
  { key: 'schedule', href: '#', icon: Calendar },
  { key: 'reports', href: '#', icon: BarChart3 },
]

const secondaryNavItems: NavItem[] = [
  { key: 'billing', href: '/billing/', icon: CreditCard },
  { key: 'notifications', href: '/notifications/', icon: Bell },
  { key: 'settings', href: '/settings/', icon: Settings },
]

function isActive(href: string, currentUrl: string): boolean {
  if (href === '#') return false
  if (href === '/dashboard/') return currentUrl === '/dashboard/' || currentUrl === '/'
  return currentUrl.startsWith(href)
}

// ============================================================================
// Main Layout
// ============================================================================

export default function DashboardLayout({ children, title }: Props) {
  const { auth, flash } = usePage<PageProps>().props
  const { url } = usePage()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const sidebarWidth = collapsed ? 'w-16' : 'w-64'
  const mainMargin = collapsed ? 'lg:ml-16' : 'lg:ml-64'

  return (
    <div className="flex h-screen bg-default-50 overflow-hidden">
      {/* ── Mobile overlay ── */}
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

      {/* ── Desktop sidebar ── */}
      <aside
        className={`hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:z-40
          ${sidebarWidth} bg-background border-r border-divider transition-all duration-300`}
      >
        <SidebarHeader collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
        <SidebarNav currentUrl={url} collapsed={collapsed} />
        <SidebarFooter user={auth.user} collapsed={collapsed} />
      </aside>

      {/* ── Main content ── */}
      <div className={`flex-1 flex flex-col h-screen overflow-hidden transition-all duration-300 ${mainMargin}`}>
        {/* Header */}
        <header className="flex-shrink-0 h-16 z-30 border-b border-divider bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center px-6 gap-4">
          {/* Mobile hamburger */}
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="lg:hidden p-2 -ml-2 rounded-lg text-default-500 hover:text-foreground hover:bg-default-100 transition-colors"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Page title */}
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-foreground">{title}</h1>
          </div>

          {/* Right side controls */}
          <div className="flex items-center gap-1">
            <LanguageSelector />
            <ThemeToggleButton />

            {/* Notifications */}
            <Link
              href="/notifications/"
              className="relative p-2 rounded-lg text-default-500 hover:text-foreground hover:bg-default-100 transition-colors"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-1.5 right-1.5 h-2.5 w-2.5 rounded-full bg-danger animate-pulse" />
            </Link>

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
  )
}

// ============================================================================
// Sidebar sub-components
// ============================================================================

function SidebarHeader({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <div className="h-16 flex items-center justify-between px-4 border-b border-divider flex-shrink-0">
      <Link href="/dashboard/" className="flex items-center gap-2.5 overflow-hidden">
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
      <button
        type="button"
        onClick={onToggle}
        className="hidden lg:flex p-1.5 rounded-lg text-default-400 hover:text-foreground hover:bg-default-100 transition-colors"
      >
        <ChevronLeft className={`h-4 w-4 transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
      </button>
    </div>
  )
}

function SidebarNav({
  currentUrl,
  collapsed,
  onNavigate,
}: {
  currentUrl: string
  collapsed: boolean
  onNavigate?: () => void
}) {
  const { t } = useTranslation('common')

  return (
    <nav className="flex-1 overflow-y-auto p-3 space-y-6">
      {/* Main */}
      <div className="space-y-1">
        {!collapsed && (
          <p className="px-3 mb-2 text-xs font-semibold text-default-400 uppercase tracking-wider">
            {t('nav.principal', 'Principal')}
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
  )
}

function NavLink({
  item,
  currentUrl,
  collapsed,
  onNavigate,
}: {
  item: NavItem
  currentUrl: string
  collapsed: boolean
  onNavigate?: () => void
}) {
  const { t } = useTranslation('common')
  const active = isActive(item.href, currentUrl)
  const label = t(`nav.${item.key}`, item.key)

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
        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-white/80" />
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
              {item.badge.label}
            </Chip>
          )}
        </>
      )}
    </Link>
  )

  if (collapsed) {
    return <div title={label}>{content}</div>
  }
  return content
}

function SidebarFooter({ user, collapsed }: { user: PageProps['auth']['user']; collapsed: boolean }) {
  return (
    <div className="p-3 border-t border-divider flex-shrink-0">
      {!collapsed ? (
        <div className="flex items-center gap-3">
          <Avatar size="sm" className="flex-shrink-0">
            <Avatar.Fallback className="bg-gradient-primary text-white text-xs font-medium">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </Avatar.Fallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{user?.name}</p>
            <p className="text-xs text-default-400 truncate">{user?.email}</p>
          </div>
          <Link
            href="/auth/logout/"
            method="post"
            as="button"
            className="p-1.5 rounded-lg text-default-400 hover:text-danger hover:bg-danger/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <Link
          href="/auth/logout/"
          method="post"
          as="button"
          title="Logout"
          className="flex items-center justify-center p-2.5 rounded-lg text-default-400 hover:text-danger hover:bg-danger/10 transition-colors w-full"
        >
          <LogOut className="w-4 h-4" />
        </Link>
      )}
    </div>
  )
}

// ============================================================================
// Header sub-components
// ============================================================================

function ThemeToggleButton() {
  const { resolvedTheme, setTheme } = useTheme()
  return (
    <button
      type="button"
      onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-lg text-default-500 hover:text-foreground hover:bg-default-100 transition-colors"
    >
      {resolvedTheme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  )
}

function UserDropdown({ user }: { user: PageProps['auth']['user'] }) {
  return (
    <Dropdown>
      <Dropdown.Trigger>
        <button
          type="button"
          className="hidden lg:flex items-center gap-2 rounded-lg p-2 hover:bg-default-100 transition-colors"
        >
          <Avatar size="sm">
            <Avatar.Fallback className="bg-gradient-primary text-white text-xs font-medium">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </Avatar.Fallback>
          </Avatar>
          <div className="hidden xl:block text-left">
            <p className="text-sm font-medium text-foreground truncate max-w-[120px]">
              {user?.name}
            </p>
          </div>
          <ChevronDown className="h-4 w-4 text-default-400" />
        </button>
      </Dropdown.Trigger>
      <Dropdown.Popover placement="bottom end">
        <Dropdown.Menu>
          <Dropdown.Item id="profile" onAction={() => router.visit('/settings/profile/')}>
            <div className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              <span>Profile Settings</span>
            </div>
          </Dropdown.Item>
          <Dropdown.Item id="help">
            <div className="flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              <span>Help & Support</span>
            </div>
          </Dropdown.Item>
          <Dropdown.Item id="logout" onAction={() => router.post('/auth/logout/')}>
            <div className="flex items-center gap-2 text-danger">
              <LogOut className="h-4 w-4" />
              <span>Sign Out</span>
            </div>
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown.Popover>
    </Dropdown>
  )
}

// ============================================================================
// Flash messages
// ============================================================================

function FlashMessages({ flash }: { flash: PageProps['flash'] }) {
  if (!flash?.success && !flash?.error && !flash?.warning && !flash?.info) return null

  return (
    <div className="px-6 pt-4 space-y-2">
      {flash.success && (
        <div className="p-3 bg-success/10 text-success-700 dark:text-success-400 rounded-xl text-sm border border-success/20 animate-slide-up">
          {flash.success}
        </div>
      )}
      {flash.error && (
        <div className="p-3 bg-danger/10 text-danger-700 dark:text-danger-400 rounded-xl text-sm border border-danger/20 animate-slide-up">
          {flash.error}
        </div>
      )}
      {flash.warning && (
        <div className="p-3 bg-warning/10 text-warning-700 dark:text-warning-400 rounded-xl text-sm border border-warning/20 animate-slide-up">
          {flash.warning}
        </div>
      )}
      {flash.info && (
        <div className="p-3 bg-primary/10 text-primary-700 dark:text-primary-400 rounded-xl text-sm border border-primary/20 animate-slide-up">
          {flash.info}
        </div>
      )}
    </div>
  )
}
