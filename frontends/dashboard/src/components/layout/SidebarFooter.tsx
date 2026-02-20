/**
 * SidebarFooter — User info card + logout action at bottom of sidebar.
 */

import { Link } from '@inertiajs/react';
import { Avatar } from '@heroui/react';
import { LogOut } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { SidebarUser } from './sidebar-nav-config';

interface Props {
  user: SidebarUser;
  collapsed: boolean;
}

export function SidebarFooter({ user, collapsed }: Props) {
  const { t } = useTranslation('common');
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
          title={t('nav.signOut', 'Sign Out')}
          className="flex items-center justify-center p-2.5 rounded-lg text-default-400 hover:text-danger hover:bg-danger/10 transition-colors w-full"
        >
          <LogOut className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}
